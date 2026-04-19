def get_type(path: str) -> str:
    type=input(f"""
获取设备类型的功能还没实现，请手动填入
1:ssd
2:hdd
3:tf card
4x:tape:lto-x
5:others
please input the number:
""")
    if type == "1":
        return "SSD".lower()
    elif type == "2":
        return "HDD".lower()
    elif type == "3":
        return "TF_SD_CARD".lower()
    elif type.startswith("4"):
        return f"Tape-lto{type.replace("4", "")}".lower()
    elif type == "None":
        return None
    else:
        raise ValueError("Invalid type")