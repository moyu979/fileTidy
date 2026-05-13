def get_file_system(path:str) -> str:
    raw = input(
        f"自动检测文件系统的功能还没实现，请按数字选择\n{path}\n1: ntfs\n请输入选项编号: "
    ).strip()
    n = int(raw)
    if n == 1:
        return "ntfs"
    raise ValueError(f"无效选项 {n!r}，目前仅支持 1（ntfs）")
