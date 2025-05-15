import win32com.client

def get_physical_disk_info():
    """
    获取硬盘的物理信息，包括序列号、型号、制造商等。
    :return: 包含硬盘信息的列表
    """
    try:
        disk_info_list = []
        wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        service = wmi.ConnectServer(".", "root\\cimv2")
        disks = service.ExecQuery("SELECT * FROM Win32_DiskDrive")

        for disk in disks:
            for prop in disk.Properties_:
                print(f"{prop.Name}: {prop.Value}")
            #break
        return disk_info_list
    except Exception as e:
        return {"error": str(e)}

# 示例调用
disk_info = get_physical_disk_info()
for info in disk_info:
    print(info)