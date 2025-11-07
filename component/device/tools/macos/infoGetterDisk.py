"""
获取磁盘信息
"""

import os
import logging
from utils.runCommand import run_command
from .isHdd import is_hdd
from .isSSD import is_ssd

logger = logging.getLogger(__name__)


def get_serial(dev_path):
    """获取设备序列号"""
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
            # 从 smartctl 输出中提取序列号
            for line in out.splitlines():
                if "Serial Number:" in line or "Serial number:" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        return parts[1].strip()
        
        # smartctl 不可用，使用 diskutil
        cmd = ["diskutil", "info", device_path]
        code, out, err = run_command(cmd)
        if code != 0:
            logger.warning(f"获取序列号失败，设备: {device_path}, 错误: {err}")
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
    except Exception as e:
        logger.warning(f"获取序列号异常，设备: {dev_path}, 错误: {str(e)}")
        return None
    return None


def get_size(dev_path):
    """获取设备容量（字节）"""
    try:
        # 规范化设备路径为 /dev/diskN 格式
        if dev_path.startswith('/dev/disk'):
            device_path = dev_path
        elif dev_path.startswith('disk'):
            device_path = f'/dev/{dev_path}'
        else:
            return None
        
        # 使用 diskutil info 获取容量
        cmd = ["diskutil", "info", device_path]
        code, out, err = run_command(cmd)
        if code != 0:
            logger.warning(f"获取容量失败，设备: {device_path}, 错误: {err}")
            return None
        
        # 从 diskutil 输出中提取容量
        for line in out.splitlines():
            if "Disk Size:" in line or "Total Size:" in line:
                # 格式通常是 "Disk Size: 500.1 GB (500107862016 Bytes)"
                # 提取括号中的字节数
                if "(" in line and "Bytes" in line:
                    parts = line.split("(")
                    if len(parts) > 1:
                        size_part = parts[1].split("Bytes")[0].strip()
                        # 移除逗号并转换为整数
                        size_str = size_part.replace(",", "").strip()
                        if size_str.isdigit():
                            return int(size_str)
    except Exception as e:
        logger.warning(f"获取容量异常，设备: {dev_path}, 错误: {str(e)}")
        return None
    return None


def get_device_info(dev_path):
    """获取单个设备的完整信息"""
    serial = get_serial(dev_path)
    size = get_size(dev_path)
    
    # 规范化设备路径为 /dev/diskN 格式
    if dev_path.startswith('/dev/disk'):
        device_path = dev_path
    elif dev_path.startswith('disk'):
        device_path = f'/dev/{dev_path}'
    else:
        device_path = dev_path
    
    return {
        "id": serial,
        "size": size,
        "path": device_path
    }


def get_disk(path):
    """
    获取指定路径的磁盘信息。
    
    Args:
        path: 磁盘设备路径，支持格式：
            - /dev/disk0, /dev/disk1
            - disk0, disk1 (自动添加 /dev/ 前缀)
    
    Returns:
        字典格式的磁盘信息，如果路径不存在或不是有效的磁盘设备则返回 None：
        {
            "id": "序列号值",
            "size": 容量字节数,
            "path": "/dev/设备名"
        }
    """
    if path is None:
        logger.error("路径参数不能为 None")
        return None
    
    path = str(path).strip()
    if not path:
        logger.error("路径参数不能为空")
        return None
    
    # 规范化设备路径为 /dev/diskN 格式
    if path.startswith('/dev/disk'):
        device_path = path
    elif path.startswith('disk'):
        device_path = f'/dev/{path}'
    else:
        logger.warning(f"不支持的设备路径格式: {path}")
        return None
    
    # 检查设备文件是否存在
    if not os.path.exists(device_path):
        logger.warning(f"设备路径不存在: {device_path}")
        return None
    
    # 使用 is_hdd 和 is_ssd 判断是否为有效的磁盘设备
    if not (is_hdd(path) or is_ssd(path)):
        logger.warning(f"不是有效的磁盘设备路径（非HDD或SSD）: {path}")
        return None
    
    return get_device_info(path)

