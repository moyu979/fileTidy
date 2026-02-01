def get_type(device_path):
    type=input(f"""
get_type func on macos not finished, please input it manually
device_path is {device_path}
1:ssd
2:hdd
3:tf card
4:tape
please input the number:
""")
    if type == "1":
        return "SSD".lower()
    elif type == "2":
        return "HDD".lower()
    elif type == "3":
        return "TF Card".lower()
    elif type.startswith("4"):
        return f"Tape-lto{type.replace("x", "")}".lower()
    elif type == "None":
        return None
    else:
        raise ValueError("Invalid type")
    
if __name__ == "__main__":
    print(get_type("/dev/disk0"))