import os
def serial2path(serial):
    path=input(f"""
serial2path func on macos not finished, please input it manually
serial is {serial}
please input the device path:
""")
    if path == "None":
        return None
    else:
        return path
if __name__ == "__main__":
    print(serial2path("1008611"))