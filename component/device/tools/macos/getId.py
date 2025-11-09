"""
输入磁盘路径，返回磁盘序列号
"""

from utils.runCommand import run_command


def get_id(dev_path):
    """输入磁盘路径，返回磁盘序列号"""
    try:
        # 规范化设备路径为 /dev/diskN 格式
        if dev_path.startswith('/dev/disk'):
            device_path = dev_path
        elif dev_path.startswith('disk'):
            device_path = f'/dev/{dev_path}'
        else:
            return None
        
        # 优先使用 smartctl 获取序列号
        cmd = ["sudo", "smartctl", "-i", device_path]
        code, out, err = run_command(cmd)
        if code == 0:
            for line in out.splitlines():
                if "Serial Number:" in line or "Serial number:" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        return parts[1].strip()
        
        # smartctl 不可用，使用 diskutil
        cmd = ["diskutil", "info", device_path]
        code, out, err = run_command(cmd)
        if code != 0:
            return None
        
        # 从 diskutil 输出中提取序列号
        for line in out.splitlines():
            if "Volume UUID:" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
            elif "Disk / Partition UUID:" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
    except Exception:
        return None
    return None

