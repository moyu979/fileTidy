"""
检查传入的目录是否是一个有效的挂载点（独立的文件系统）
"""

import os


def is_mount_point(path):
    """
    检查路径是否是一个挂载点（独立的文件系统）
    
    Args:
        path: 要检查的路径
    
    Returns:
        bool: 如果是挂载点返回 True，否则返回 False
    """
    if not path:
        return False
    
    try:
        # 规范化路径
        path = os.path.abspath(os.path.expanduser(path))
        
        # 检查路径是否存在
        if not os.path.exists(path):
            return False
        
        # 获取路径的 stat 信息
        path_stat = os.stat(path)
        path_dev = path_stat.st_dev
        
        # 获取父目录的 stat 信息
        parent_path = os.path.dirname(path.rstrip('/'))
        # 如果已经是根目录，则认为是挂载点
        if parent_path == path or parent_path == '/':
            return True
        
        try:
            parent_stat = os.stat(parent_path)
            parent_dev = parent_stat.st_dev
        except (OSError, IOError):
            # 如果无法访问父目录，可能是挂载点
            return True
        
        # 如果设备 ID 不同，说明是挂载点
        return path_dev != parent_dev
    except (OSError, IOError):
        return False

