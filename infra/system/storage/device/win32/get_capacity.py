# CHECK: AI生成 - win32 平台：获取设备容量
"""win32 —— 获取设备容量。"""

from ._common import _get_drive_by_path


def get_capacity(path: str) -> int:
    """获取设备容量（字节）。

    Args:
        path: 设备路径。

    Returns:
        设备容量（字节）。

    Raises:
        ValueError: 无法获取容量时抛出。
    """
    drive = _get_drive_by_path(path)
    if drive and "Size" in drive:
        return int(drive["Size"])
    raise ValueError(f"无法获取容量: {path}")
