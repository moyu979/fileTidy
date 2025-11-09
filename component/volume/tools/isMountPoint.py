"""
检查传入的目录是否是一个有效的挂载点（独立的文件系统）
"""

from utils.confs import get_conf_manager


def is_mount_point(path):
    """
    检查路径是否是一个挂载点（独立的文件系统）
    
    Args:
        path: 要检查的路径
    
    Returns:
        bool: 如果是挂载点返回 True，否则返回 False
    """
    system = get_conf_manager().get("system")
    
    if system == "windows":
        from .windows.isMountPoint import is_mount_point as impl
    elif system == "linux":
        from .linux.isMountPoint import is_mount_point as impl
    elif system == "macos":
        from .macos.isMountPoint import is_mount_point as impl
    else:
        raise ValueError(f"不支持的系统: {system}")
    
    if impl is None:
        raise ValueError("获取平台对应的模块失败")
    
    return impl(path)


__all__ = [
    "is_mount_point",
]

