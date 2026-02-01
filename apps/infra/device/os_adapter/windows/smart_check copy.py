def smart_check(device_path):
    result=input(f"""
path2serial func on macos not finished, please input it manually
device_path is {device_path}
tell me the result of smart check:
01:health
02:danger
03:unknown
""")
    if result == "1":
        return "health"
    elif type == "2":
        return "danger"
    elif type == "3":
        return "unknown"
    elif result == "None":
        return None
    else:
        raise ValueError("Invalid type")
    return result
if __name__ == "__main__":
    print(smart_check("/dev/disk0"))