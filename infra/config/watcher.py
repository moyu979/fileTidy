# CHECK: AI生成 - 共享配置监听器（方案 A：单 Observer + 单 handler 按路径分发）
# 说明：
#   - 由配置系统顶端的 config 手动实例化一个 ConfigWatcher（传入配置根目录），
#     注入到各子配置类共用，只占一份监听线程（1 个 emitter + 1 个派发线程）。
#   - 对配置根目录 schedule 一次，handler 按事件 src_path 分发到已注册的 reload 回调。
#   - watchdog 不可用时自动降级为单个轮询线程。

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

# 去抖间隔（秒）—— 防止编辑器连续保存触发多次重载
_DEBOUNCE_INTERVAL: float = 0.3
# 轮询降级时的检查间隔（秒）
_POLL_INTERVAL: float = 60.0


class ConfigWatcher:
    """共享配置监听器。

    监听配置根目录（settings_dir），事件按文件路径分发到对应 reload()。
    由配置系统顶端手动实例化并注入各子配置类共用。
    首次 register() 自动启动监听；stop() 停止。
    """

    def __init__(self, settings_dir: str | Path) -> None:
        """初始化监听器，记录配置根目录。

        Args:
            settings_dir (str | Path): 配置根目录。
        """
        self.settings_dir = Path(settings_dir).expanduser().resolve()
        self._lock = threading.RLock()
        self._reload_map: dict[str, Callable[[], bool]] = {}   # 绝对路径 -> reload 回调
        self._last_reload: dict[str, float] = {}               # 路径 -> 上次重载时间（去抖）
        self._observer: Any | None = None                      # watchdog Observer
        self._handler: Any | None = None                       # watchdog 事件 handler
        self._poll_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._poll_interval: float = _POLL_INTERVAL

    def register(self, file_path: str | Path, reload_fn: Callable[[], bool]) -> None:
        """注册配置文件及对应 reload 回调（同路径重复注册覆盖）。

        首次注册时自动启动监听。

        Args:
            file_path (str | Path): 配置文件路径。
            reload_fn (Callable[[], bool]): 无参回调，文件变化时调用（如 config.reload）。
        """
        path = Path(file_path).expanduser().resolve()
        with self._lock:
            self._reload_map[str(path)] = reload_fn
        self.start()
        logger.info("ConfigWatcher 注册监听: %s", path)

    def unregister(self, file_path: str | Path) -> None:
        """注销一个配置文件的监听。

        Args:
            file_path (str | Path): 配置文件路径。
        """
        path = Path(file_path).expanduser().resolve()
        with self._lock:
            self._reload_map.pop(str(path), None)
            self._last_reload.pop(str(path), None)

    def start(self) -> None:
        """启动监听：watchdog 优先，不可用时降级为单个轮询线程（幂等）。"""
        with self._lock:
            if self._observer is not None or self._poll_thread is not None:
                return
            self._observer = self._setup_file_watcher()
            if self._observer is not None:
                logger.info(
                    "ConfigWatcher 文件监听已启动: %s", self.settings_dir
                )
            else:
                self._stop_event.clear()
                self._poll_thread = threading.Thread(
                    target=self._poll_loop,
                    name="config-watcher-poll",
                    daemon=True,
                )
                self._poll_thread.start()
                logger.info(
                    "ConfigWatcher 轮询已启动，间隔 %.0f 秒", self._poll_interval
                )

    def stop(self, timeout: float | None = None) -> None:
        """停止监听：停止 watchdog Observer 与轮询线程。

        Args:
            timeout (float | None): 等待线程结束的超时时间（秒）；None 表示无限等待。
        """
        if self._observer is not None:
            try:
                self._observer.stop()
                self._observer.join(timeout=timeout)
            except Exception as exc:
                logger.exception("停止 ConfigWatcher observer 异常: %s", exc)
            self._observer = None
            self._handler = None
            logger.info("ConfigWatcher 文件监听已停止")
        if self._poll_thread is not None:
            self._stop_event.set()
            self._poll_thread.join(timeout=timeout)
            self._poll_thread = None
            logger.info("ConfigWatcher 轮询已停止")

    @property
    def is_running(self) -> bool:
        """任一监听机制是否正在运行。

        Returns:
            bool: 是否运行。
        """
        return (self._observer is not None and self._observer.is_alive()) or (
            self._poll_thread is not None and self._poll_thread.is_alive()
        )

    def _handle(self, src_path: str) -> None:
        """按事件源路径分发到已注册的 reload 回调（带去抖）。

        锁内查找回调与去抖判断，锁外执行 reload，避免死锁。

        Args:
            src_path (str): 事件源文件路径。
        """
        key = str(Path(src_path).expanduser().resolve())
        now = time.time()
        with self._lock:
            reload_fn = self._reload_map.get(key)
            if reload_fn is None:
                return
            if now - self._last_reload.get(key, 0.0) < _DEBOUNCE_INTERVAL:
                return
            self._last_reload[key] = now
        try:
            reload_fn()
        except Exception as exc:
            logger.exception("配置 reload 回调执行失败: %s", exc)

    def _setup_file_watcher(self) -> Any | None:
        """创建单个 Observer + 单 handler，监听配置根目录一次。

        Returns:
            Any | None: watchdog Observer；watchdog 不可用或目录不存在时返回 None（改用轮询）。
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            logger.warning(
                "watchdog 未安装，配置热更降级为轮询模式。安装: pip install watchdog"
            )
            return None

        if not self.settings_dir.is_dir():
            logger.warning(
                "配置根目录不存在，无法建立 watchdog 监听: %s", self.settings_dir
            )
            return None

        class _Handler(FileSystemEventHandler):
            """按事件 src_path 分发到对应配置。"""

            def __init__(self, watcher: ConfigWatcher) -> None:
                """记录所属 watcher。

                Args:
                    watcher (ConfigWatcher): 所属监听器。
                """
                self._watcher = watcher

            def _route(self, event: Any) -> None:
                """过滤目录与非 yaml 事件，路由到对应配置。

                Args:
                    event (Any): watchdog 事件。
                """
                if event.is_directory:
                    return
                if not event.src_path.endswith((".yaml", ".yml")):
                    return
                self._watcher._handle(event.src_path)

            def on_modified(self, event: Any) -> None:
                """文件修改事件路由。

                Args:
                    event (Any): watchdog 事件。
                """
                self._route(event)

            def on_created(self, event: Any) -> None:
                """文件创建事件路由。

                Args:
                    event (Any): watchdog 事件。
                """
                self._route(event)

            def on_deleted(self, event: Any) -> None:
                """文件删除事件路由。

                Args:
                    event (Any): watchdog 事件。
                """
                self._route(event)

            def on_moved(self, event: Any) -> None:
                """文件移动事件路由（原子保存场景：目标文件才是被注册的）。

                Args:
                    event (Any): watchdog 移动事件，含 src/dest 路径。
                """
                # 原子保存（临时文件重命名覆盖）场景：目标文件才是被注册的
                self._watcher._handle(event.dest_path)
                self._watcher._handle(event.src_path)

        self._handler = _Handler(self)
        observer = Observer()
        observer.schedule(self._handler, str(self.settings_dir), recursive=False)
        observer.start()
        logger.info("ConfigWatcher 文件监听已启动 (watchdog): %s", self.settings_dir)
        return observer

    def _poll_loop(self) -> None:
        """单轮询线程：定时对每个已注册文件调用 _handle。

        变化判断交由 reload 内部按 mtime 进行。
        """
        while not self._stop_event.is_set():
            with self._lock:
                paths = list(self._reload_map.keys())
            for path in paths:
                self._handle(path)
            waited = 0.0
            step = min(1.0, self._poll_interval)
            while waited < self._poll_interval:
                if self._stop_event.wait(timeout=step):
                    return
                waited += step
