def get_volume_serial_by_path(path: str) -> str | None:
    serial = input(
        f"根据路径自动获取所属 volume serial 的功能还没实现，请手动输入\n"
        f"路径: {path}\n"
        f"所属 volume serial（留空表示不属于任何已知卷）: "
    ).strip()
    if serial == "":
        return None
    return serial
