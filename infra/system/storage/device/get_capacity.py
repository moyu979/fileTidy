# CHECK: AI生成 - device 转发：获取设备容量
"""device —— 转发到当前平台：获取设备容量。"""

from infra.system.runtime import current_platform

from ._util import as_device_path


def get_capacity(path_or_serial: str) -> int:
    """获取设备容量（支持传路径或序列号）。

    Args:
        path_or_serial: 设备路径或序列号。

    Returns:
        设备容量（字节）。

    Raises:
        ValueError: 无法将入参解析为设备路径时抛出。
    """
    return current_platform().get_capacity(as_device_path(path_or_serial))
