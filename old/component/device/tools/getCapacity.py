"""
输入磁盘路径，返回磁盘容量
"""

from utils.confs import get_conf_manager


def get_capacity(dev_path):
    """
    输入磁盘路径，返回磁盘容量
    
    Args:
        dev_path: 硬盘设备路径，格式取决于操作系统：
            - Linux: /dev/sda, /dev/nvme0n1 等
            - Windows: \\.\PhysicalDrive0, PhysicalDrive0, 0 等
            - macOS: /dev/disk0, disk0 等
    
    Returns:
        int: 磁盘容量（字节），如果获取失败则返回 None
    """
    system = get_conf_manager().get("system")
    
    if system == "windows":
        from .windows.getCapacity import get_capacity as impl
    elif system == "linux":
        from .linux.getCapacity import get_capacity as impl
    elif system == "macos":
        from .macos.getCapacity import get_capacity as impl
    else:
        raise ValueError(f"不支持的系统: {system}")
    
    if impl is None:
        raise ValueError("获取平台对应的模块失败")
    
    return impl(dev_path)


__all__ = [
    "get_capacity",
]

