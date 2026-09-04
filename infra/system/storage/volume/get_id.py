# CHECK: 待检查 - 系统卷 ID 获取 - 读取卷标识符

def get_id(path: str) -> str:
    """
    获取指定路径对应的卷 ID（占位实现：由用户手动输入）。

    Args:
        path: 卷路径

    Returns:
        卷 ID，输入空字符则返回 None
    """
    id=input(f"get id for {path}: 的功能还没实现，请手动填入，输入空字符以做None")
    if id == "":
        return None
    return id