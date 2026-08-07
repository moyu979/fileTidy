# CHECK: AI生成 - linux 平台：获取设备序列号
"""linux —— 获取设备序列号。"""

from ._common import _disk_info


def get_serial(path: str) -> str | None:
    """获取设备的序列号。

    Args:
        path: 设备路径。

    Returns:
        设备序列号字符串，未找到时返回 None。
    """
    info = _disk_info(path)
    return info.get("serial") or None
