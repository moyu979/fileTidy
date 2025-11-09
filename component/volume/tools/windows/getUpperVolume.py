"""
从给定路径向上遍历，查找满足条件的挂载点（Windows 版本）
"""

import os
import re
from ..isMountPoint import is_mount_point


def get_upper_volume(file_path):
    """
    从文件路径开始，向上遍历父目录，查找满足条件的挂载点
    
    条件：
    1. 是一个挂载点
    2. 有一个 "info" 子目录
    3. "info" 子目录里有一个文件名格式为 "id+任意位数字" 的文件
    
    Args:
        file_path: 起始文件路径
    
    Returns:
        tuple: (volume_path, volume_id) 如果找到，否则返回 (None, None)
        volume_path: 满足条件的挂载点路径
        volume_id: 从文件名中提取的序列号（数字部分）
    """
    if not file_path:
        return None, None
    
    try:
        # 规范化路径
        current_path = os.path.abspath(os.path.expanduser(file_path))
        
        # 如果是文件，从父目录开始检查
        if os.path.isfile(current_path):
            current_path = os.path.dirname(current_path)
        
        # 向上遍历目录树
        while current_path:
            # 检查是否是挂载点
            if is_mount_point(current_path):
                # 检查是否有 info 子目录
                info_dir = os.path.join(current_path, "info")
                if os.path.isdir(info_dir):
                    # 遍历 info 目录中的文件
                    try:
                        for filename in os.listdir(info_dir):
                            # 检查文件名格式：id + 任意位数字
                            match = re.match(r'^id(\d+)$', filename)
                            if match:
                                volume_id = match.group(1)
                                return current_path, volume_id
                    except (OSError, IOError):
                        # 无法读取目录，继续向上
                        pass
            
            # 获取父目录
            parent_path = os.path.dirname(current_path)
            
            # 如果父目录和当前目录相同，说明已经到达根目录
            if parent_path == current_path:
                break
            
            current_path = parent_path
        
        return None, None
    except (OSError, IOError):
        return None, None

