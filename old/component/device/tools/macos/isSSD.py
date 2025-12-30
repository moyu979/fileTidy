import os
from utils.runCommand import run_command


def is_ssd(device: str) -> bool:
    """判断设备是否为SSD"""
    if not device:
        return False
    
    # 规范化设备路径为 /dev/diskN 格式
    if device.startswith('/dev/disk'):
        device_path = device
    elif device.startswith('disk'):
        device_path = f'/dev/{device}'
    else:
        return False
    
    # 检查设备文件是否存在
    if not os.path.exists(device_path):
        return False
    
    # 使用 diskutil info 查询 Solid State
    cmd = ["diskutil", "info", device_path]
    code, out, err = run_command(cmd)
    if code != 0:
        return False
    
    # 查找 "Solid State: Yes" 表示 SSD
    for line in out.splitlines():
        if "Solid State:" in line:
            return "Yes" in line
    return False

