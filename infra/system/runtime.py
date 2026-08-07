# CHECK: AI生成 - system infra 运行时：OS 状态 + 平台分发
"""system infra 运行时 —— OS 状态 + 平台分发。

在 bootstrap 初始化阶段手动调用 :func:`init_sys_infra` 注入配置；
device 等子系统通过 :func:`current_platform` 按当前 OS 加载对应平台包。
"""

from __future__ import annotations

import importlib
import sys
from typing import Any

# OS 名 → 平台包模块名（未知回退 unknown）
_PLATFORMS: dict[str, str] = {
    "darwin": "darwin",
    "linux": "linux",
    "win32": "win32",
    "unknown": "unknown",
}

_os: str | None = None                  # 由 init_sys_infra / set_os 设置的显式 OS
_platform_modules: dict[str, Any] = {}  # 「子系统.平台」→ 已加载的平台模块（缓存）


def init_sys_infra(conf) -> None:
    """初始化 system infra（手动调用）。

    从配置读取操作系统（``system.platform``，即 ``sys.platform``），
    并失效平台模块缓存，使后续 :func:`current_platform` 按新 OS 加载。

    Args:
        conf: AppConfig 实例（含 ``system`` section）。
    """
    global _os
    _os = conf.get("system", "platform", "unknown")
    _platform_modules.clear()


def set_os(name: str) -> None:
    """显式指定操作系统（测试 / 脚本模拟用）。

    Args:
        name: 操作系统名，如 ``"darwin"``、``"linux"``、``"win32"``。
    """
    global _os
    _os = name
    _platform_modules.clear()


def current_os() -> str:
    """返回当前操作系统标识。

    优先级：显式设置（init_sys_infra / set_os）> ``sys.platform``。

    Returns:
        操作系统标识字符串。
    """
    return _os if _os is not None else sys.platform


def resolve_platform(os_name: str | None = None) -> str:
    """将操作系统名解析为平台包模块名。

    Args:
        os_name: 操作系统名；缺省取 :func:`current_os`。

    Returns:
        平台包模块名；未知 OS 回退 ``"unknown"``。
    """
    return _PLATFORMS.get(os_name or current_os(), "unknown")


def current_platform(group: str = "device") -> Any:
    """按当前 OS 加载指定子系统的平台模块（lazy 加载并缓存）。

    Args:
        group: 子系统名，如 ``"device"``、``"volume"``、``"file"``；
               对应 ``infra.system.storage.<group>/`` 下的平台包。

    Returns:
        当前 OS 对应的平台包模块（含 6 个设备操作函数）。
    """
    key = f"{group}.{resolve_platform()}"
    module = _platform_modules.get(key)
    if module is None:
        module = importlib.import_module(
            f"infra.system.storage.{group}.{resolve_platform()}"
        )
        _platform_modules[key] = module
    return module


def reset() -> None:
    """失效全部平台模块缓存（测试用，下一次调用重新加载）。"""
    _platform_modules.clear()
