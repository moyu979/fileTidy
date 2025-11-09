"""
将输入路径规范化成 /dev/* 设备路径
支持格式：/dev/sda, /dev/nvme0n1, /dev/st0 等
"""


def get_normalized_path(dev_path):
    """
    将输入路径规范化成 /dev/* 设备路径
    
    Args:
        dev_path: 设备路径，支持格式：
            - /dev/sda, /dev/nvme0n1, /dev/st0 等（完整路径）
            - sda, nvme0n1, st0 等（设备名，自动添加 /dev/ 前缀）
    
    Returns:
        str: 规范化后的设备路径，如 /dev/sda
        None: 如果输入格式不支持
    """
    if not dev_path:
        return None
    
    dev_path = dev_path.strip()
    
    # 如果已经是 /dev/ 开头的完整路径，直接返回
    if dev_path.startswith('/dev/'):
        return dev_path
    
    # 如果是设备名（如 sda, nvme0n1, st0），添加 /dev/ 前缀
    # 检查是否为有效的设备名格式（不包含路径分隔符）
    if '/' not in dev_path and dev_path:
        return f'/dev/{dev_path}'
    
    # 其他情况返回 None
    return None