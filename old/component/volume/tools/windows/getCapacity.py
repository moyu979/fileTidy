"""
获取挂载点容量（字节）
"""

import os
import shutil
from .isMountPoint import is_mount_point


def get_capacity(mount_point):
    """
    获取挂载点容量（字节）
    
    Args:
        mount_point: 挂载点路径（如 C:\ 或挂载的目录）
    
    Returns:
        int: 挂载点容量（字节），如果获取失败或不是挂载点则返回 None
    """
    if not mount_point:
        return None
    
    try:
        # 规范化路径
        mount_point = os.path.abspath(os.path.expanduser(mount_point))
        
        # 检查是否为挂载点
        if not is_mount_point(mount_point):
            return None
        
        # 检查路径是否存在
        if not os.path.exists(mount_point):
            return None
        
        # 使用 shutil.disk_usage 获取磁盘使用情况
        # 返回 (total, used, free)，单位是字节
        usage = shutil.disk_usage(mount_point)
        total_capacity = usage.total
        
        return total_capacity
    except (OSError, IOError, AttributeError) as e:
        return None

