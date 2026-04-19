def get_path(serial: str) -> str:
    input_path = input(f"get device path for {serial}: 的功能还没实现，请手动填入，输入空字符以做None")
    if input_path == "":
        return None
    return input_path