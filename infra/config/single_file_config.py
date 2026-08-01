# CHECK: AI生成 - 单文件配置通用类（热更新，共享 ConfigWatcher）

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from infra.config.watcher import ConfigWatcher

import yaml

from infra.config.interface import ConfigContentManager

logger = logging.getLogger(__name__)


class SingleFileConfig(ConfigContentManager):
    """单个 YAML 配置文件的内容管理实现，支持热更新与 ``${key}`` 占位符替换。

    实现 ``ConfigContentManager`` 纯接口；锁、热更框架（mtime 检测 / on_change /
    watcher 注册）与占位符替换（替换表由 AppConfig 注入）均在本类
    内部。构造即注册热更监听。读取 fail-fast：必填项用 ``config[key]`` /
    ``get_required()``（缺失抛 KeyError），可选项才用 ``get(key, default=None)``。
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
        self._change_callbacks: list[Callable[[list[str]], None]] = []
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

    def on_change(self, callback: Callable[[list[str]], None]) -> None:
        """注册变更回调。

        Args:
            callback (Callable[[list[str]], None]): 收到变化的键名列表。
        """
        self._change_callbacks.append(callback)

    def _notify_change(self, changed_keys: list[str]) -> None:
        """通知变更回调（在锁外调用）。

        Args:
            changed_keys (list[str]): 变化的键名列表。
        """
        for cb in self._change_callbacks:
            try:
                cb(changed_keys)
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
