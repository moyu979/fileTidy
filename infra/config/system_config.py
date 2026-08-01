# TEST 需要在windows，linux和freebsd系统上进行测试
# CHECK: AI生成 - SystemConfig 懒调用：方法注册表 + 实时系统调用（实现 ConfigContentManager）

from __future__ import annotations

import logging
import os
import platform
import socket
import sys
from pathlib import Path
from typing import Any, Callable, NamedTuple

import psutil

# 允许直接运行（python infra/config/system_config.py）: 将项目根目录加入 sys.path，
# 以便导入 infra / shared 等顶层模块；作为库导入时此块不执行
if __name__ == "__main__":
    _project_root = Path(__file__).resolve().parent.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

from infra.config.interface import ConfigContentManager

logger = logging.getLogger(__name__)


class MemoryInfo(NamedTuple):
    """系统内存信息快照。"""

    total: int        # 物理内存总量（字节）
    used: int         # 已使用内存（字节）
    available: int    # 可用内存（字节）
    percent: float    # 使用率（0~100）
    process_rss: int  # 当前进程常驻内存（字节）


class SystemConfig(ConfigContentManager):
    """系统配置读取器（懒调用：方法注册表 + 实时系统调用）。

    实现 ``ConfigContentManager`` 纯接口。每个配置项对应一个直接系统调用的 getter，
    注册在内置字典 ``_methods``，取数时按 key 查表并调用返回（无缓存、无锁、
    reload 无操作）。获取的 key 与数据内容与原静态方法完全一致。

    取数流程::

        config.get("hostname")     # 查 _methods → 无此 key 返回 default
        config["platform"]         # __getitem__ → 无此 key 抛 KeyError
        config.get_required("cpu_count")
        "cpu_count" in config
        config.data                 # 实时全量快照
        config.get_memory_used()    # 专用 getter：直接系统调用

    工作流与设计思路见 ``docs/infra/config/system_config.md``。
    """

    def __init__(self) -> None:
        """注册各配置项对应的实时系统调用 getter。"""
        self._methods: dict[str, Callable[[], Any]] = {
            "hostname": self.get_hostname,
            "platform": self.get_platform,
            "platform_info": self.get_platform_info,
            "python_version": self.get_python_version,
            "cpu_count": self.get_cpu_count,
            "is_64bit": self.is_64bit,
            "pid": self.get_pid,
            "cwd": self.get_cwd,
            "process": self.get_process_name,
            "mem_total": self.get_memory_total,
            "mem_used": self.get_memory_used,
            "mem_available": self.get_memory_available,
            "mem_percent": self.get_memory_percent,
            "process_rss": self.get_process_memory,
        }
        logger.info("SystemConfig constructed")

    def get(self, key: str, default: Any = None) -> Any:
        """宽松读取：查 _methods，无此 key 返回 default，有则调用返回。

        Args:
            key (str): 配置项键名。
            default (Any): 缺失时返回的默认值。

        Returns:
            Any: 对应 getter 的返回值，或 default。
        """
        method = self._methods.get(key)
        return method() if method is not None else default

    def get_required(self, key: str) -> Any:
        """严格读取：无此 key 抛 KeyError，有则调用返回。

        Args:
            key (str): 配置项键名。

        Returns:
            Any: 对应 getter 的返回值。

        Raises:
            KeyError: key 未注册时。
        """
        method = self._methods.get(key)
        if method is None:
            raise KeyError(f"缺少配置项 {key!r}")
        return method()

    def __getitem__(self, key: str) -> Any:
        """按 key 读取（config[key]）。

        Args:
            key (str): 配置项键名。

        Returns:
            Any: 对应 getter 的返回值。

        Raises:
            KeyError: key 未注册时。
        """
        method = self._methods.get(key)
        if method is None:
            raise KeyError(f"缺少配置项 {key!r}")
        return method()

    def __contains__(self, key: object) -> bool:
        """判断配置项是否注册。

        Args:
            key (object): 配置项键名。

        Returns:
            bool: 是否注册。
        """
        return key in self._methods

    @property
    def data(self) -> dict[str, Any]:
        """实时调用全部已注册 getter，返回全量配置快照。

        Returns:
            dict[str, Any]: 全部配置项。
        """
        return {key: method() for key, method in self._methods.items()}

    def reload(self) -> bool:
        """无缓存可刷新（实时取数），本操作无效果。

        Returns:
            bool: 恒为 False。
        """
        return False

    def get_hostname(self) -> str:
        """获取主机名。

        Returns:
            str: 主机名。
        """
        return socket.gethostname()

    def get_platform(self) -> str:
        """获取操作系统平台标识（``sys.platform``）。

        Returns:
            str: 平台标识。
        """
        return sys.platform

    def get_platform_info(self) -> str:
        """获取详细操作系统版本信息。

        Returns:
            str: 版本信息。
        """
        return platform.platform()

    def get_python_version(self) -> str:
        """获取 Python 解释器版本信息。

        Returns:
            str: 版本信息。
        """
        return sys.version

    def get_cpu_count(self) -> int:
        """获取逻辑 CPU 核心数（获取失败时返回 1）。

        Returns:
            int: 核心数。
        """
        return os.cpu_count() or 1

    def is_64bit(self) -> bool:
        """判断当前 Python 解释器是否为 64 位（通过 ``sys.maxsize`` 判断）。

        Returns:
            bool: 是否 64 位。
        """
        return sys.maxsize > 2**32

    def get_pid(self) -> int:
        """获取当前进程 PID。

        Returns:
            int: PID。
        """
        return os.getpid()

    def get_cwd(self) -> str:
        """获取当前工作目录。

        Returns:
            str: 目录路径。
        """
        return os.getcwd()

    def get_process_name(self) -> str:
        """获取当前进程名称（``sys.argv[0]`` 的文件名部分）。

        Returns:
            str: 进程名。
        """
        return Path(sys.argv[0]).name if sys.argv else ""

    def get_memory_total(self) -> int:
        """获取物理内存总量。

        Returns:
            int: 字节数。
        """
        return int(psutil.virtual_memory().total)

    def get_memory_used(self) -> int:
        """获取已使用的物理内存。

        Returns:
            int: 字节数。
        """
        return int(psutil.virtual_memory().used)

    def get_memory_available(self) -> int:
        """获取可用物理内存。

        Returns:
            int: 字节数。
        """
        return int(psutil.virtual_memory().available)

    def get_memory_percent(self) -> float:
        """获取内存使用率。

        Returns:
            float: 使用率（0~100）。
        """
        return float(psutil.virtual_memory().percent)

    def get_process_memory(self) -> int:
        """获取当前进程常驻内存 RSS。

        Returns:
            int: 字节数。
        """
        return int(psutil.Process().memory_info().rss)

    def get_memory_info(self) -> MemoryInfo:
        """返回完整内存信息快照（单次采样，避免多次调用产生不一致数据）。

        Returns:
            MemoryInfo: 内存信息。
        """
        vm = psutil.virtual_memory()
        return MemoryInfo(
            total=int(vm.total),
            used=int(vm.used),
            available=int(vm.available),
            percent=float(vm.percent),
            process_rss=int(psutil.Process().memory_info().rss),
        )

    def summary(self) -> dict[str, Any]:
        """返回常用信息摘要（实时取数）。

        Returns:
            dict[str, Any]: 摘要。
        """
        data = self.data
        return {
            "hostname": data["hostname"],
            "platform": data["platform"],
            "platform_info": data["platform_info"],
            "python_version": str(data["python_version"]).split()[0],
            "cpu_count": data["cpu_count"],
            "is_64bit": data["is_64bit"],
            "pid": data["pid"],
            "cwd": data["cwd"],
            "process": data["process"],
            "mem_total": data["mem_total"],
            "mem_used": data["mem_used"],
            "mem_available": data["mem_available"],
            "mem_percent": data["mem_percent"],
            "process_rss": data["process_rss"],
        }


def main() -> None:
    """演示 SystemConfig 懒调用取数接口并打印摘要。"""
    # 允许直接运行本文件（python infra/config/system_config.py）:
    # 将项目根目录加入 sys.path，以便导入 infra.common 等模块
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from infra.common.capacity_converter import format_capacity

    config = SystemConfig()

    print("=" * 60)
    print("SystemConfig 懒调用（方法注册表 + 实时系统调用）")
    print("=" * 60)
    print(f"  get('hostname')   : {config.get('hostname')}")
    print(f"  get_hostname()    : {config.get_hostname()}")
    print(f"  get_platform()    : {config.get_platform()}")
    print(f"  get_platform_info(): {config.get_platform_info()}")
    print(f"  get_python_version(): {config.get_python_version().split()[0]}")
    print(f"  get_cpu_count()   : {config.get_cpu_count()}")
    print(f"  is_64bit()        : {config.is_64bit()}")
    print(f"  get_pid()         : {config.get_pid()}")
    print(f"  get_cwd()         : {config.get_cwd()}")
    print(f"  get_process_name(): {config.get_process_name()}")
    print(f"  config['platform']: {config['platform']}")
    print(f"  'cpu_count' in config: {'cpu_count' in config}")
    try:
        config["missing_key"]
    except KeyError as exc:
        print(f"  config['missing_key'] -> KeyError: {exc}")

    print()
    print("=" * 60)
    print("摘要 summary()（实时取数）")
    print("=" * 60)
    for key, value in config.summary().items():
        if key in ("mem_total", "mem_used", "mem_available", "process_rss"):
            value = f"{format_capacity(value, base=1024)} ({value} B)"
        print(f"  {key:16}: {value}")

    mem = config.get_memory_info()
    # 内存按二进制（1024）显示，与硬盘的千进制（1000）区分
    print()
    print("内存信息 get_memory_info()（单次采样）:")
    print(f"  mem_total    : {format_capacity(mem.total, base=1024)} ({mem.total} B)")
    print(f"  mem_used     : {format_capacity(mem.used, base=1024)} ({mem.used} B)")
    print(f"  mem_available: {format_capacity(mem.available, base=1024)} ({mem.available} B)")
    print(f"  mem_percent  : {mem.percent:.1f}%")
    print(f"  process_rss  : {format_capacity(mem.process_rss, base=1024)} ({mem.process_rss} B)")


if __name__ == "__main__":
    main()
