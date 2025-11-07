"""
获取磁盘信息
"""

import logging
from utils.runCommand import run_command
from .isHdd import is_hdd
from .isSSD import is_ssd

logger = logging.getLogger(__name__)


def get_serial(dev_path):
    """获取设备序列号"""
    try:
        # 规范化设备路径，提取设备号
        device_num = None
        if dev_path.isdigit():
            device_num = dev_path
        elif dev_path.startswith('PhysicalDrive'):
            device_num = dev_path.replace('PhysicalDrive', '')
        elif dev_path.startswith(r'\\.\PhysicalDrive'):
            device_num = dev_path.replace(r'\\.\PhysicalDrive', '')
        else:
            return None
        
        # 使用 PowerShell 获取序列号
        ps_cmd = [
            'powershell', '-Command',
            f'$disk = Get-PhysicalDisk -DeviceNumber {device_num} -ErrorAction SilentlyContinue; '
            f'if ($disk) {{ Write-Output $disk.SerialNumber }}'
        ]
        code, out, err = run_command(ps_cmd)
        if code != 0 or not out.strip():
            logger.warning(f"获取序列号失败，设备: {dev_path}, 错误: {err}")
            return None
        return out.strip()
    except Exception as e:
        logger.warning(f"获取序列号异常，设备: {dev_path}, 错误: {str(e)}")
        return None


def get_size(dev_path):
    """获取设备容量（字节）"""
    try:
        # 规范化设备路径，提取设备号
        device_num = None
        if dev_path.isdigit():
            device_num = dev_path
        elif dev_path.startswith('PhysicalDrive'):
            device_num = dev_path.replace('PhysicalDrive', '')
        elif dev_path.startswith(r'\\.\PhysicalDrive'):
            device_num = dev_path.replace(r'\\.\PhysicalDrive', '')
        else:
            return None
        
        # 使用 PowerShell 获取容量（字节）
        ps_cmd = [
            'powershell', '-Command',
            f'$disk = Get-PhysicalDisk -DeviceNumber {device_num} -ErrorAction SilentlyContinue; '
            f'if ($disk) {{ Write-Output $disk.Size }}'
        ]
        code, out, err = run_command(ps_cmd)
        if code != 0 or not out.strip():
            logger.warning(f"获取容量失败，设备: {dev_path}, 错误: {err}")
            return None
        size_str = out.strip()
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
    
    # 规范化设备路径
    if dev_path.isdigit():
        device_path = rf'\\.\PhysicalDrive{dev_path}'
    elif dev_path.startswith('PhysicalDrive'):
        device_path = rf'\\.\{dev_path}'
    elif dev_path.startswith(r'\\.\PhysicalDrive'):
        device_path = dev_path
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
            - \\.\PhysicalDrive0, \\.\PhysicalDrive1
            - PhysicalDrive0, PhysicalDrive1
            - 0, 1, 2 (设备号，自动转换为 \\.\PhysicalDriveN)
    
    Returns:
        字典格式的磁盘信息，如果路径不存在或不是有效的磁盘设备则返回 None：
        {
            "id": "序列号值",
            "size": 容量字节数,
            "path": "设备路径"
        }
    """
    if path is None:
        logger.error("路径参数不能为 None")
        return None
    
    path = str(path).strip()
    if not path:
        logger.error("路径参数不能为空")
        return None
    
    # 规范化设备路径
    if path.isdigit():
        device_path = rf'\\.\PhysicalDrive{path}'
    elif path.startswith('PhysicalDrive'):
        device_path = rf'\\.\{path}'
    elif path.startswith(r'\\.\PhysicalDrive'):
        device_path = path
    else:
        logger.warning(f"不支持的设备路径格式: {path}")
        return None
    
    # 使用 is_hdd 和 is_ssd 判断是否为有效的磁盘设备
    if not (is_hdd(path) or is_ssd(path)):
        logger.warning(f"不是有效的磁盘设备路径（非HDD或SSD）: {path}")
        return None
    
    return get_device_info(path)

