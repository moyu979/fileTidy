# CHECK: AI生成 - win32 平台：获取设备序列号
"""win32 —— 获取设备序列号。"""

from ._common import _get_drive_by_path


def get_serial(path: str) -> str | None:
    """获取设备的序列号。

    Args:
        path: 设备路径。

    Returns:
        设备序列号字符串，未找到时返回 None。
    """
    drive = _get_drive_by_path(path)
    if drive:
        return drive.get("SerialNumber", "").strip() or None
    return None
