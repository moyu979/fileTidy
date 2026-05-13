def get_volume_capacity(path) -> int | None:
    raw = input(
        f"自动获取卷容量的功能还没实现，请自行输入\n请输入 {path} 的capacity（字节整数，留空表示未知）: "
    ).strip()
    if raw == "":
        return None
    return int(raw)
