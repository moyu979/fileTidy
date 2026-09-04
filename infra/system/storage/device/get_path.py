# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - device 转发：获取设备路径
"""device —— 转发到当前平台：获取设备路径。"""

from infra.system.runtime import current_platform


def get_path(serial: str) -> str | None:
    """获取指定序列号对应的设备路径。

    Args:
        serial: 设备序列号。

    Returns:
        设备路径。
    """
    return current_platform().get_path(serial)
