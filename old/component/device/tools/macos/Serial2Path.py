"""
根据给出的硬盘序列号，返回对应的设备路径，如果没有挂载这个序列号，返回None
"""

import subprocess
from utils.runCommand import run_command
from .getSerial import get_serial


def serial_to_path(serial):
    """
    根据序列号查找对应的设备路径
    
    Args:
        serial: 硬盘序列号
    
    Returns:
        str: 设备路径（如 /dev/disk0），如果未找到则返回 None
    """
    if not serial:
        return None
    
    try:
        # 使用 diskutil list 获取所有磁盘
        cmd = ["diskutil", "list"]
        code, out, err = run_command(cmd)
        if code != 0:
            return None
        
        # 解析 diskutil list 输出，提取所有磁盘设备
        devices = []
        for line in out.splitlines():
            # diskutil list 输出格式通常是：/dev/disk0 (internal, physical)
            if '/dev/disk' in line and 'physical' in line.lower():
                parts = line.split()
                for part in parts:
                    if part.startswith('/dev/disk') and part[9:].isdigit():
                        devices.append(part)
                        break
        
        # 遍历所有设备，查找匹配的序列号
        for dev_path in devices:
            try:
                device_serial = get_serial(dev_path)
                if device_serial and device_serial.strip() == serial.strip():
                    return dev_path
            except Exception:
                # 忽略单个设备的错误，继续查找
                continue
    except Exception:
        pass
    
    return None

