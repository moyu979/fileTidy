"""
获取挂载点容量（字节）
"""

import os
from .isMountPoint import is_mount_point


def get_capacity(mount_point):
    """
    获取挂载点容量（字节）
    
    Args:
        mount_point: 挂载点路径
    
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
        
        # 使用 statvfs 获取文件系统统计信息
        stat = os.statvfs(mount_point)
        
        # 总容量 = 块数 * 块大小（字节）
        # f_blocks: 文件系统中总块数
        # f_frsize: 文件系统块大小（优先使用，更准确）
        # f_bsize: 文件系统块大小（备选）
        total_capacity = stat.f_blocks * (stat.f_frsize if hasattr(stat, 'f_frsize') else stat.f_bsize)
        
        return total_capacity
    except (OSError, IOError, AttributeError) as e:
        return None

