# CHECK: AI生成 - device 转发：获取设备健康状态
"""device —— 转发到当前平台：获取设备健康状态。"""

from domain.storage.device.enum import DeviceState
from infra.system.runtime import current_platform

from ._util import as_device_path


def get_healthy(path_or_serial: str) -> DeviceState:
    """获取设备健康状态（支持传路径或序列号）。

    Args:
        path_or_serial: 设备路径或序列号。

    Returns:
        DeviceState 枚举值。

    Raises:
        ValueError: 无法将入参解析为设备路径时抛出。
    """
    return current_platform().get_healthy(as_device_path(path_or_serial))
