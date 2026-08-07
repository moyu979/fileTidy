# CHECK: AI生成 - unknown 平台：获取设备类型（占位）
"""unknown —— 获取设备类型（占位：菜单选择）。"""

from infra.system.runtime import current_os


def get_type(path: str) -> str:
    """获取设备类型（占位实现：由用户通过菜单手动选择）。

    支持的类型：SSD、HDD、TF 卡、磁带（LTO 系列）等。

    Args:
        path: 设备路径。

    Returns:
        设备类型字符串。

    Raises:
        ValueError: 输入的类型编号无效。
    """
    type_input = input(
        f"获取设备类型的功能还没实现（{current_os()} 系统下），请手动填入\n"
        f"1:ssd\n2:hdd\n3:tf card\n4x:tape:lto-x\n5:others\n"
        f"please input the number: "
    )
    if type_input == "1":
        return "SSD".lower()
    elif type_input == "2":
        return "HDD".lower()
    elif type_input == "3":
        return "TF_SD_CARD".lower()
    elif type_input.startswith("4"):
        return f"Tape-lto{type_input.replace('4', '')}".lower()
    elif type_input == "None":
        return None
    else:
        raise ValueError("Invalid type")
