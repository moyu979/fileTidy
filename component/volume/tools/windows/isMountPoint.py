"""
检查传入的目录是否是一个有效的挂载点（独立的文件系统）
"""

import os
import ctypes
from ctypes import wintypes


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
        
        # 获取路径的规范形式（去除尾随分隔符）
        normalized_path = os.path.normpath(path)
        
        # 检查是否是驱动器根目录（如 C:\）
        if len(normalized_path) == 3 and normalized_path[1] == ':' and normalized_path[2] == '\\':
            return True
        
        # 使用 GetVolumePathName 检查
        # 如果路径的卷路径与路径本身相同，说明是挂载点
        kernel32 = ctypes.windll.kernel32
        
        # 获取当前路径的卷路径
        volume_path = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        if not kernel32.GetVolumePathNameW(normalized_path, volume_path, wintypes.MAX_PATH):
            # API 调用失败，回退到简单检查
            return False
        
        volume_path_str = os.path.normpath(volume_path.value)
        # 如果卷路径与当前路径相同，说明是挂载点
        if volume_path_str.lower() == normalized_path.lower():
            return True
        
        # 获取父目录的卷路径进行比较
        parent_path = os.path.dirname(normalized_path)
        if parent_path == normalized_path:
            # 已经是根目录
            return True
        
        parent_volume_path = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        if kernel32.GetVolumePathNameW(parent_path, parent_volume_path, wintypes.MAX_PATH):
            parent_volume_path_str = os.path.normpath(parent_volume_path.value)
            # 如果父目录的卷路径与当前路径的卷路径不同，说明是挂载点
            if parent_volume_path_str.lower() != volume_path_str.lower():
                return True
        
        return False
    except (OSError, IOError, AttributeError):
        # 如果 API 调用失败，回退到简单检查
        try:
            # 检查是否是驱动器根目录
            normalized_path = os.path.normpath(path)
            if len(normalized_path) == 3 and normalized_path[1] == ':' and normalized_path[2] == '\\':
                return True
            return False
        except:
            return False

