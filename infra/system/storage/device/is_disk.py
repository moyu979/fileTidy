def is_disk(path: str) -> bool:
    input(f"""
    检查路径是否是磁盘的挂载点，的功能还没写好，请手动输入：
    yes: 是
    no: 否
    """)
    if input == "yes" or input == "y":
        return True
    else:
        return False