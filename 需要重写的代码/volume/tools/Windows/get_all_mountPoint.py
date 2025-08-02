import wmi


def get_all_mount_points_with_wmi():
    """
    使用 WMI 获取所有挂载点及其详细信息，包括挂载到文件夹的卷。
    :return: 挂载点及详细信息的列表
    """
    c = wmi.WMI()
    volumes = []
    for volume in c.Win32_Volume():
        volumes.append(
            {
                "mount_point": volume.Name,  # 挂载点（可能是驱动器号或文件夹路径）
                "fs_type": volume.FileSystem,  # 文件系统类型（如 NTFS、FAT32）
                "volume_name": volume.Label,  # 卷标
                "size": volume.Capacity,  # 总容量（字节）
                "free_space": volume.FreeSpace,  # 可用空间（字节）
            }
        )
    return volumes


# 示例调用
mount_points = get_all_mount_points_with_wmi()
for mount in mount_points:
    print(mount)
