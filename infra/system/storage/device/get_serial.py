# CHECK: AI生成 - device 转发：获取设备序列号
"""device —— 转发到当前平台：获取设备序列号。"""

from infra.system.runtime import current_platform


def get_serial(path: str) -> str | None:
    """获取指定路径对应的设备序列号。

    Args:
        path: 设备路径。

    Returns:
        设备序列号。
    """
    return current_platform().get_serial(path)
