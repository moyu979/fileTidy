import os
import subprocess


def is_direct_partition_mount(path):
    # 1. 判断是否挂载点
    if subprocess.run(["mountpoint", "-q", path]).returncode != 0:
        return False, None

    # 2. 获取挂载设备（分区）
    result = subprocess.run(
        ["findmnt", "-n", "-o", "SOURCE", "--target", path],
        capture_output=True,
        text=True,
    )
    device = result.stdout.strip()

    # 3. 判断设备是否是分区块设备
    if (
        device.startswith("/dev/")
        and os.path.exists(device)
        and os.stat(device).st_mode & 0o60000 == 0o60000
    ):
        type_result = subprocess.run(
            ["lsblk", "-no", "TYPE", device], capture_output=True, text=True
        )
        if type_result.stdout.strip() == "part":
            return True, device

    return False, device


def get_disk_from_partition(partition):
    # 使用 lsblk 获取分区的父设备名（磁盘）
    result = subprocess.run(
        ["lsblk", "-no", "pkname", partition], capture_output=True, text=True
    )
    parent = result.stdout.strip()
    if parent:
        return f"/dev/{parent}"
    else:
        return None


def is_partition(path):
    is_partition, device = is_direct_partition_mount(path)
    if is_partition:
        disk = get_disk_from_partition(device)
    else:
        disk = None
    return is_partition, device, disk
