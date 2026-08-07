# CHECK: AI生成 - darwin 平台：获取设备类型
"""darwin —— 获取设备类型。"""

from ._common import _disk_info


def get_type(path: str) -> str:
    """获取设备类型。

    根据 Solid State / Removable Media 判断类型。

    Args:
        path: 设备路径。

    Returns:
        设备类型字符串："ssd", "hdd", "tf_sd_card"。
    """
    info = _disk_info(path)
    solid = info.get("Solid State", "").lower()
    removable = info.get("Removable Media", "").lower()

    if removable == "removable":
        return "tf_sd_card"
    if solid == "yes":
        return "ssd"
    return "hdd"  # 默认 HDD
