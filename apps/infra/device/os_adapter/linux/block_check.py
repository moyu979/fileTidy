def block_check(device_path):
    result=input(f"""
block_check func on linux not finished, please input it manually
device_path is {device_path}
tell me the result of block check:
1:health
2:danger
3:unknown
""")
    if result == "1":
        return "health"
    elif result == "2":
        return "danger"
    elif result == "3":
        return "unknown"
    elif result == "None":
        return None
    else:
        raise ValueError("Invalid result")
if __name__ == "__main__":
    print(block_check("/dev/disk0"))