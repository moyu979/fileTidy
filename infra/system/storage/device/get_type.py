# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - device 转发：获取设备类型
"""device —— 转发到当前平台：获取设备类型。"""

from infra.system.runtime import current_platform

from ._util import as_device_path


def get_type(path_or_serial: str) -> str:
    """获取设备类型（支持传路径或序列号）。

    Args:
        path_or_serial: 设备路径或序列号。

    Returns:
        设备类型字符串。

    Raises:
        ValueError: 无法将入参解析为设备路径时抛出。
    """
    return current_platform().get_type(as_device_path(path_or_serial))
