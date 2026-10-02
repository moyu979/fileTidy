from __future__ import annotations

import logging
import threading
import weakref
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from infra.config.watcher import ConfigWatcher

import yaml

from infra.config.interface import ConfigContentManager

logger = logging.getLogger(__name__)


class SingleFileConfig(ConfigContentManager):
    """单个 YAML 配置文件的内容管理实现，支持热更新与 ``${key}`` 占位符替换。

    实现 ``ConfigContentManager`` 纯接口；锁、热更框架（mtime 检测 / subscribe /
    watcher 注册）与占位符替换（替换表由 AppConfig 注入）均在本类
    内部。构造即注册热更监听。读取 fail-fast：必填项用 ``config[key]`` /
    ``get_required()``（缺失抛 KeyError），可选项才用 ``get(key, default=None)``。

    订阅（``subscribe`` / ``unsubscribe``）以**弱引用**持有回调，订阅者被释放后
    自动失效，不会因注册过回调而无法回收。代价是回调必须是 Python 定义的
    bound method 且其所有者可弱引用——lambda、普通函数与 C 内置方法会被拒绝
    （见 ``subscribe``）。
    """

    def __init__(
        self,
        path: str | Path,
        watcher: "ConfigWatcher",
        replacements: dict[str, str] | None = None,
    ) -> None:
        """加载配置并注册热更监听。

        Args:
            path (str | Path): 配置文件路径。
            watcher (ConfigWatcher): 共享的配置监听器。
            replacements (dict[str, str] | None): 可选，``${key}`` 占位符替换表
                （由 AppConfig 参数透传）。

        Raises:
            FileNotFoundError: 配置文件缺失。
            yaml.YAMLError: YAML 解析失败。
            ValueError: YAML 根节点不是映射。
        """
        self.path = Path(path).expanduser().resolve()
        self._replacements = dict(replacements) if replacements else {}
        self._lock = threading.RLock()          # 允许信号/监听回调安全重入
        self._data: dict[str, Any] = {}
        self._mtime: float | None = None
        # 弱引用持有：订阅者被回收后自动失效，无需显式 unsubscribe
        self._change_callbacks: list[weakref.WeakMethod] = []
        self._watcher = watcher
        self.load()
        watcher.register(self.path, self.reload)
        logger.info("SingleFileConfig constructed: path=%s", self.path)

    def get(self, key: str, default: Any = None) -> Any:
        """宽松读取配置项，仅用于可选项。

        Args:
            key (str): 配置项键名。
            default (Any): 缺失时返回的默认值。

        Returns:
            Any: 配置项的值，或 default。
        """
        with self._lock:
            return self._data.get(key, default)

    def get_required(self, key: str) -> Any:
        """严格读取必填项。

        Args:
            key (str): 配置项键名。

        Returns:
            Any: 配置项的值。

        Raises:
            KeyError: key 缺失时（错误信息含配置文件路径）。
        """
        with self._lock:
            if key in self._data:
                return self._data[key]
        raise KeyError(f"缺少必填配置项 {key!r}（配置文件: {self.path}）")

    def __getitem__(self, key: str) -> Any:
        """按 key 读取（config[key]）。

        Args:
            key (str): 配置项键名。

        Returns:
            Any: 配置项的值。

        Raises:
            KeyError: key 缺失时（错误信息含配置文件路径）。
        """
        with self._lock:
            if key in self._data:
                return self._data[key]
        raise KeyError(f"缺少配置项 {key!r}（配置文件: {self.path}）")

    def __contains__(self, key: object) -> bool:
        """判断配置项是否存在于 YAML。

        Args:
            key (object): 配置项键名。

        Returns:
            bool: 是否存在。
        """
        with self._lock:
            return key in self._data

    @property
    def data(self) -> dict[str, Any]:
        """当前配置的拷贝。

        Returns:
            dict[str, Any]: 全部配置项拷贝。
        """
        with self._lock:
            return dict(self._data)

    def stop_auto_reload(self) -> None:
        """从共享 ConfigWatcher 注销本文件监听（幂等）。"""
        self._watcher.unregister(self.path)
        logger.info("SingleFileConfig 自动热更已停止: %s", self.path)

    @property
    def is_auto_reload_running(self) -> bool:
        """共享 watcher 是否正在运行。

        Returns:
            bool: 是否运行。
        """
        return self._watcher.is_running

    def load(self) -> dict[str, Any]:
        """读取并解析 YAML，整体替换当前配置。

        Returns:
            dict[str, Any]: 新配置数据。

        Raises:
            FileNotFoundError: 配置文件缺失。
            yaml.YAMLError: YAML 解析失败。
            ValueError: YAML 根节点不是映射。
        """
        if not self.path.is_file():
            raise FileNotFoundError(f"配置文件不存在: {self.path}")

        data = self._replace_placeholders(self._read_yaml())
        with self._lock:
            self._data = data
            self._update_mtime()
        return dict(data)

    def reload(self) -> bool:
        """热重载：文件有变化才重读，失败保留旧配置。

        Returns:
            bool: 是否有变化；解析失败时保留旧配置并返回 False。
        """
        if not self._has_changed():
            return False

        try:
            data = self._replace_placeholders(self._read_yaml())
        except (ValueError, yaml.YAMLError, OSError) as exc:
            logger.error("配置重载失败，保留旧配置: %s", exc)
            with self._lock:
                self._update_mtime()
            return False

        with self._lock:
            old = self._data
            changed = sorted(
                (set(old) ^ set(data))
                | {k for k in set(old) & set(data) if old[k] != data[k]}
            )
            self._data = data
            self._update_mtime()

        if changed:
            logger.info("配置发生变化: %s", changed)
            self._notify_change(changed)

        return True

    def _read_yaml(self) -> dict[str, Any]:
        """读取并解析 YAML 内容（根节点必须是 dict）。

        Returns:
            dict[str, Any]: 解析结果。

        Raises:
            ValueError: YAML 根节点不是映射。
        """
        text = self.path.read_text(encoding="utf-8")
        raw = yaml.safe_load(text) if text.strip() else {}
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise ValueError(
                f"{self.path} 根节点必须是映射（dict），实际为 {type(raw).__name__}"
            )
        return raw

    def _has_changed(self) -> bool:
        """文件 mtime 是否变化。

        Returns:
            bool: 是否变化；stat 失败视为变化。
        """
        try:
            return self.path.stat().st_mtime != self._mtime
        except OSError:
            return True

    def _update_mtime(self) -> None:
        """刷新 mtime 快照。"""
        try:
            self._mtime = self.path.stat().st_mtime
        except OSError:
            self._mtime = None

    def subscribe(self, callback: Callable[[list[str]], None]) -> None:
        """订阅配置变更（弱引用持有，订阅者被释放后自动失效）。

        回调必须是 Python 定义的 **bound method**（如 ``obj.handle``），且其所有者
        可弱引用：以 ``weakref.WeakMethod`` 只弱引用所有者，所有者被回收后引用
        自动变为空，通知时跳过，无需手动退订。

        校验直接交给 ``weakref.WeakMethod``（EAFP）：lambda 与普通函数没有所有者
        对象（弱引用会立即失效从而静默不触发）、C 内置方法（如 ``list.append``）
        不受支持、所有者不可弱引用（如未声明 ``__weakref__`` 的 ``__slots__``
        实例）——三者都在注册时抛出，具体原因见异常的 ``__cause__``。

        Args:
            callback (Callable[[list[str]], None]): bound method，收到变化的键名列表。

        Raises:
            TypeError: callback 不是 Python bound method，或其所有者不可弱引用。
        """
        try:
            weak_callback = weakref.WeakMethod(callback)
        except TypeError as exc:
            raise TypeError(
                f"subscribe 只接受「Python 定义且所有者可弱引用的对象方法」"
                f"（如 obj.handle），当前回调不满足：{type(callback).__name__}"
            ) from exc
        with self._lock:
            # 顺手回收已释放订阅者的空引用，避免列表随订阅者更迭而累积
            self._change_callbacks = [
                ref for ref in self._change_callbacks if ref() is not None
            ]
            self._change_callbacks.append(weak_callback)
        # 只记录名字，不传 callback 本体：LogRecord 会持有 args，
        # 若被 handler 长期保留，就成了隐式强引用，弱引用随即失效。
        logger.debug(
            "订阅配置变更: %s.%s",
            type(callback.__self__).__name__,
            callback.__name__,
        )

    def unsubscribe(self, callback: Callable[[list[str]], None]) -> None:
        """取消订阅（幂等；未订阅过时什么也不做）。

        传入与 ``subscribe`` 相同的对象方法即可：bound method 按
        ``(所有者, 函数)`` 比较相等，因此重新求值的表达式也能命中。

        Args:
            callback (Callable[[list[str]], None]): 要退订的对象方法。
        """
        with self._lock:
            kept: list[weakref.WeakMethod] = []
            removed = False
            for ref in self._change_callbacks:
                target = ref()
                if target is None:
                    continue                       # 已释放，顺手丢弃
                if not removed and target == callback:
                    removed = True
                    continue                       # 命中目标，丢弃
                kept.append(ref)
            self._change_callbacks = kept
        if removed:
            logger.debug(
                "取消订阅配置变更: %s.%s",
                type(callback.__self__).__name__,
                callback.__name__,
            )

    def _notify_change(self, changed_keys: list[str]) -> None:
        """通知已订阅的回调（在锁外调用；自动跳过已释放的订阅者）。

        Args:
            changed_keys (list[str]): 变化的键名列表。
        """
        with self._lock:
            refs = list(self._change_callbacks)    # 快照，避免遍历期间被改
        for ref in refs:
            callback = ref()
            if callback is None:
                continue                           # 订阅者已释放，跳过
            try:
                callback(changed_keys)
            except Exception as exc:
                logger.exception("配置变更回调执行失败: %s", exc)

    def _replace_placeholders(self, obj: Any) -> Any:
        """递归替换 ``${key}`` 占位符（按 replacements 表）。

        Args:
            obj (Any): 任意结构（str/dict/list/tuple）。

        Returns:
            Any: 替换后的结构；替换表为空时原样返回。
        """
        if not self._replacements:
            return obj
        if isinstance(obj, str):
            for key, value in self._replacements.items():
                obj = obj.replace(f"${{{key}}}", str(value))
            return obj
        if isinstance(obj, dict):
            return {k: self._replace_placeholders(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._replace_placeholders(v) for v in obj]
        if isinstance(obj, tuple):
            return tuple(self._replace_placeholders(v) for v in obj)
        return obj
