def smart_check(device_path):
    result=input(f"""
smart_check func on linux not finished, please input it manually
device_path is {device_path}
tell me the result of smart check:
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
    print(smart_check("/dev/disk0"))