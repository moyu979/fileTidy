# CHECK: 待检查 - 系统文件大小获取 - 读取文件大小信息
# NOTE: file 子系统未完成（设计未定稿），此工具仅供 file 模块使用，可能随 file 一起调整。

import os


def get_file_size(path: str) -> int:
    """
    获取文件的大小（字节计）
    
    Args:
        path: 文件路径
        
    Returns:
        int: 文件的大小（字节）
        
    Raises:
        FileNotFoundError: 文件不存在
        PermissionError: 没有读取权限
        OSError: 其他文件系统错误
        ValueError: 路径是目录而不是文件
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件不存在: {path}")
    
    if os.path.isdir(path):
        raise ValueError(f"路径是目录而不是文件: {path}")
    
    if not os.path.isfile(path):
        raise ValueError(f"路径既不是文件也不是目录: {path}")
    
    try:
        return os.path.getsize(path)
    except PermissionError:
        raise PermissionError(f"没有权限访问文件: {path}")
    except OSError as e:
        raise OSError(f"获取文件大小失败 {path}: {e}")
