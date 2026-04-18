def path2serial(device_path):
    serial=input(f"""
path2serial func on macos not finished, please input it manually
device_path is {device_path}
please input the serial number:
""")
    
    return serial
if __name__ == "__main__":
    print(path2serial("/dev/disk0"))