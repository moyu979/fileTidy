"""
获取挂载点容量（字节）
"""

from utils.confs import get_conf_manager


def get_capacity(mount_point):
    """
    获取挂载点容量（字节）
    
    Args:
        mount_point: 挂载点路径，格式取决于操作系统：
            - Linux: /mnt/disk1, /media/usb 等
            - Windows: C:\, D:\ 或挂载的目录
            - macOS: /Volumes/disk1, /mnt/disk1 等
    
    Returns:
        int: 挂载点容量（字节），如果获取失败或不是挂载点则返回 None
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
    
    return impl(mount_point)


__all__ = [
    "get_capacity",
]

