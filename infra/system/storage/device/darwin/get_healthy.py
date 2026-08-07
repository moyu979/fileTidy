# CHECK: AI生成 - darwin 平台：获取设备健康状态
"""darwin —— 获取设备健康状态。"""

from domain.storage.device.enum import DeviceState

from ._common import _disk_info


def get_healthy(path: str) -> DeviceState:
    """获取设备健康状态。

    解析 SMART Status 字段。

    Args:
        path: 设备路径。

    Returns:
        DeviceState 枚举值。
    """
    info = _disk_info(path)
    status = info.get("SMART Status", "").lower()
    if status == "verified":
        return DeviceState.HEALTHY
    if status == "failing":
        return DeviceState.FAULT
    if status in ("unsupported", "not supported"):
        return DeviceState.UNKNOWN
    return DeviceState.UNKNOWN
