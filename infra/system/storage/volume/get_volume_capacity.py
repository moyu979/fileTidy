# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 系统卷容量获取 - 读取卷容量信息

def get_volume_capacity(path) -> int | None:
    """
    获取指定路径对应的卷容量（占位实现：由用户手动输入）。

    Args:
        path: 卷路径

    Returns:
        卷容量（字节），留空则返回 None
    """
    raw = input(
        f"自动获取卷容量的功能还没实现，请自行输入\n请输入 {path} 的capacity（字节整数，留空表示未知）: "
    ).strip()
    if raw == "":
        return None
    return int(raw)
