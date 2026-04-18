"""
输入磁盘路径，返回磁盘序列号
"""

from apps.common.config.config import config_manager

def block_check(dev_path):
    """
    输入磁盘路径，返回磁盘序列号
    
    Args:
        dev_path: 硬盘设备路径，格式取决于操作系统：
            - Linux: /dev/sda, /dev/nvme0n1 等
            - Windows: \\.\PhysicalDrive0, PhysicalDrive0, 0 等
            - macOS: /dev/disk0, disk0 等
    
    Returns:
        str: 磁盘序列号，如果获取失败则返回 None
    """
    system = get_conf_manager().get("system")
    
    if system == "windows":
        from .windows.block_check import block_check as impl
    elif system == "linux":
        from .linux.block_check import block_check as impl
    elif system == "macos":
        from .macos.block_check import block_check as impl
    else:
        raise ValueError(f"不支持的系统: {system}")
    
    if impl is None:
        raise ValueError("获取平台对应的模块失败")
    
    return impl(dev_path)


__all__ = [
    "path2serial",
]

