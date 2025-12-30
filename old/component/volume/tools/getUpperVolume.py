"""
从给定路径向上遍历，查找满足条件的挂载点
"""

from utils.confs import get_conf_manager


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
    system = get_conf_manager().get("system")
    
    if system == "windows":
        from .windows.getUpperVolume import get_upper_volume as impl
    elif system == "linux":
        from .linux.getUpperVolume import get_upper_volume as impl
    elif system == "macos":
        from .macos.getUpperVolume import get_upper_volume as impl
    else:
        raise ValueError(f"不支持的系统: {system}")
    
    if impl is None:
        raise ValueError("获取平台对应的模块失败")
    
    return impl(file_path)


__all__ = [
    "get_upper_volume",
]

