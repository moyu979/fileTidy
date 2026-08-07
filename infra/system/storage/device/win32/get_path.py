# CHECK: AI生成 - win32 平台：根据序列号获取设备路径
"""win32 —— 根据序列号查找设备路径。"""

from ._common import _wmic


def get_path(serial: str) -> str | None:
    """根据设备序列号查找设备路径（盘符）。

    Args:
        serial: 设备序列号。

    Returns:
        盘符字符串（如 "C:"），未找到时返回 None。
    """
    drives = _wmic("diskdrive where SerialNumber=\"" + serial + "\" get Index")
    if not drives:
        return None
    idx = drives[0].get("Index", "")
    parts = _wmic(f"partition where DiskIndex={idx} get DeviceID")
    if not parts:
        return None
    logical = _wmic(
        f"logicaldisk where "
        f"assoc /assocclass:Win32_LogicalDiskToPartition"
    )
    # 解析关联结果找到盘符
    for l in logical:
        for k, v in l.items():
            if ":" in v and len(v.strip()) == 2:  # C:, D: ...
                return v.strip()
    return None
