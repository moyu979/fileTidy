"""
根据给出的硬盘序列号，返回对应的设备路径，如果没有挂载这个序列号，返回None
"""

from utils.confs import get_conf_manager


def serial_to_path(serial):
    """
    根据序列号查找对应的设备路径
    
    Args:
        serial: 硬盘序列号
    
    Returns:
        str: 设备路径，格式取决于操作系统：
            - Linux: /dev/sda, /dev/nvme0n1 等
            - Windows: \\.\PhysicalDrive0 等
            - macOS: /dev/disk0 等
        如果未找到则返回 None
    """
    system = get_conf_manager().get("system")
    
    if system == "windows":
        from .windows.Serial2Path import serial_to_path as impl
    elif system == "linux":
        from .linux.Serial2Path import serial_to_path as impl
    elif system == "macos":
        from .macos.Serial2Path import serial_to_path as impl
    else:
        raise ValueError(f"不支持的系统: {system}")
    
    if impl is None:
        raise ValueError("获取平台对应的模块失败")
    
    return impl(serial)


__all__ = [
    "serial_to_path",
]

