"""
根据给出的硬盘序列号，返回对应的设备路径，如果没有挂载这个序列号，返回None
"""

import os
import subprocess
import glob
from .getSerial import get_serial


def serial_to_path(serial):
    """
    根据序列号查找对应的设备路径
    
    Args:
        serial: 硬盘序列号
    
    Returns:
        str: 设备路径（如 /dev/sda），如果未找到则返回 None
    """
    if not serial:
        return None
    
    # 常见的块设备路径模式（只包含主设备，不包含分区）
    device_patterns = [
        '/dev/sd[a-z]',      # SATA/SCSI 磁盘
        '/dev/sd[a-z][a-z]', # 更多 SATA/SCSI 磁盘
        '/dev/nvme[0-9]n[0-9]',  # NVMe 磁盘（主设备）
        '/dev/st[0-9]',      # SCSI 磁带
        '/dev/nst[0-9]',     # 非重绕 SCSI 磁带
    ]
    
    # 收集所有可能的设备路径
    devices = []
    for pattern in device_patterns:
        devices.extend(glob.glob(pattern))
    
    # 遍历所有设备，查找匹配的序列号
    for dev_path in devices:
        try:
            # 跳过分区设备（如 nvme0n1p1）
            if 'p' in dev_path and dev_path.split('/')[-1].count('p') > 0:
                # 检查是否是分区（包含 p 后面跟数字的格式）
                parts = dev_path.split('/')[-1]
                if 'p' in parts and parts.split('p')[-1].isdigit():
                    continue
            
            device_serial = get_serial(dev_path)
            if device_serial and device_serial.strip() == serial.strip():
                return dev_path
        except Exception:
            # 忽略单个设备的错误，继续查找
            continue
    
    return None
