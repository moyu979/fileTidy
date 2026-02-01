def get_capacity(device_path):
    capacity=input(f"""
get_capacity func on linux not finished, please input it manually
device_path is {device_path}
please input the capacity (in bytes, e.g., 1000000000):
""")
    return int(capacity)
    
if __name__ == "__main__":
    print(get_capacity("/dev/disk0"))