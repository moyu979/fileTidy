# CHECK: 待检查 - 系统超级设备 ID 获取 - 读取卷所属超级设备

def get_super_device_id(path:str) -> str:
    """
    获取指定路径对应的超级设备 ID（占位实现：由用户手动输入）。

    Args:
        path: 卷路径

    Returns:
        超级设备 ID
    """
    return input(
        f"通过路径自动识别超级设备 ID 的功能还没实现，请自行输入\n{path}\n请输入 super_device_id: "
    ).strip()
