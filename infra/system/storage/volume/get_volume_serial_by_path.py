# CHECK: 待检查 - 系统卷序列号获取 - 通过路径读取卷序列号

def get_volume_serial_by_path(path: str) -> str | None:
    """
    根据路径获取所属卷的序列号（占位实现：由用户手动输入）。

    Args:
        path: 文件或目录路径

    Returns:
        卷序列号，不属于任何已知卷则返回 None
    """
    serial = input(
        f"根据路径自动获取所属 volume serial 的功能还没实现，请手动输入\n"
        f"路径: {path}\n"
        f"所属 volume serial（留空表示不属于任何已知卷）: "
    ).strip()
    if serial == "":
        return None
    return serial
