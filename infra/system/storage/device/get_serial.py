def get_serial(path: str) -> str:
    serial=input(f"get serial for {path}: 的功能还没实现，请手动填入，输入空字符以做None")
    if serial == "":
        return None
    return serial