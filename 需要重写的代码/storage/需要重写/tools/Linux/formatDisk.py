import subprocess

from storage.storage import Storage


def run_cmd(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.stdout.strip(), proc.stderr.strip(), proc.returncode


def is_disk_initialized(disk):
    out, err, code = run_cmd(["lsblk", "-ndo", "PTTYPE", "-d", disk])
    if code != 0:
        raise RuntimeError(f"读取分区表类型失败: {err}")

    if out.lower() not in ["gpt", "dos"]:
        return False

    out, err, code = run_cmd(["lsblk", "-no", "NAME", "-r", disk])
    if code != 0:
        # 读取失败，保守认为已格式化
        return True

    names = out.splitlines()
    partitions = [name for name in names if name != disk.strip("/dev/")]

    if not partitions:
        return False

    for part in partitions:
        part_path = "/dev/" + part
        out, err, code = run_cmd(["blkid", part_path])
        if code == 0 and "TYPE=" in out:
            return True

    return False


def format_disk_exfat(disk, force=False):
    """
    格式化整个磁盘为 exFAT。

    参数：
    - disk: 磁盘设备路径，如 '/dev/sdb'
    - force: 是否强制格式化，忽略磁盘当前状态

    返回：
    - True 表示格式化成功
    - False 表示格式化失败

    抛出：
    - RuntimeError 如果读取磁盘信息失败
    """
    if not force and is_disk_initialized(disk):
        raise RuntimeError(f"磁盘 {disk} 已经格式化过，未使用 force，终止操作。")

    # 创建 GPT 分区表
    out, err, code = run_cmd(["parted", "-s", disk, "mklabel", "gpt"])
    if code != 0:
        raise RuntimeError(f"创建分区表失败: {err}")

    # 创建主分区
    out, err, code = run_cmd(
        ["parted", "-s", disk, "mkpart", "primary", "fat32", "0%", "100%"]
    )
    if code != 0:
        raise RuntimeError(f"创建分区失败: {err}")

    part = disk + "1"

    # 格式化为 exFAT
    out, err, code = run_cmd(["mkfs.exfat", "-n", "MYEXFAT", part])
    if code != 0:
        raise RuntimeError(f"格式化为exFAT失败: {err}")

    return True


def format(disk: Storage, force=False):
    format_disk_exfat(disk.get_value("path"), force=force)
    disk.to_db()
