# CHECK: AI生成 - win32 平台：获取设备类型
"""win32 —— 获取设备类型。"""

from ._common import _get_drive_by_path


def get_type(path: str) -> str:
    """获取设备类型。

    Args:
        path: 设备路径。

    Returns:
        设备类型字符串："ssd", "hdd", "tf_sd_card"。

    Raises:
        ValueError: 无法获取类型时抛出。
    """
    drive = _get_drive_by_path(path)
    if drive:
        media = (drive.get("MediaType") or "").lower()
        if "ssd" in media or "solid" in media:
            return "ssd"
        if "external" in media or "removable" in media:
            if drive.get("Size", "0") < 256 * 1024**3:  # < 256GB 可能 TF
                return "tf_sd_card"
        return "hdd"
    raise ValueError(f"无法获取类型: {path}")
