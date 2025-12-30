"""
ok
文件哈希计算模块

提供文件MD5哈希值计算功能，支持单个文件和目录的批量计算。

主要功能：
    - 计算单个文件的MD5哈希值
    - 递归计算目录中所有文件的MD5哈希值
    - 支持大文件分块读取，避免内存溢出
    - 自动处理文件读取错误，目录遍历时跳过无法读取的文件

配置项：
    - hash_check_memery: 哈希计算时的块大小（MB），默认512MB

使用示例：
    >>> from utils.get_hash import get_hash
    >>> # 计算单个文件的哈希
    >>> result = get_hash("/path/to/file.txt")
    >>> # 计算目录中所有文件的哈希
    >>> results = get_hash("/path/to/directory")
"""

import hashlib
import os
from typing import List

from common.config.config import config_manager


def _hash_file(path: str) -> str:
    """
    计算文件的MD5哈希值
    
    Args:
        path: 文件路径
        
    Returns:
        str: MD5哈希值的十六进制字符串
        
    Raises:
        FileNotFoundError: 文件不存在
        PermissionError: 没有读取权限
        OSError: 其他文件系统错误
    """
    try:
        chunk_size = int(config_manager.get("hash_check_memery")) * 1024 * 1024
    except (KeyError, ValueError):
        # 默认值：512M
        chunk_size = 512 * 1024 * 1024
    hasher = hashlib.md5()
    try:
        with open(path, "rb") as stream:
            for chunk in iter(lambda: stream.read(chunk_size), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        raise
    except PermissionError:
        raise PermissionError(f"没有权限读取文件: {path}")
    except OSError as e:
        raise OSError(f"读取文件失败 {path}: {e}")


def get_hash(path: str) -> List[List[str]]:
    """
    获取文件或目录中所有文件的哈希值
    
    Args:
        path: 文件或目录路径
        
    Returns:
        List[List[str]]: 文件路径和哈希值的列表，格式为 [[path, hash], ...]
        
    Raises:
        FileNotFoundError: 路径不存在
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"路径不存在: {path}")
    
    if os.path.isfile(path):
        try:
            return [[path, _hash_file(path)]]
        except (PermissionError, OSError) as e:
            # 对于单个文件，直接抛出异常
            raise
    
    if os.path.isdir(path):
        result = []
        for root, _, files in os.walk(path):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    result.append([file_path, _hash_file(file_path)])
                except (PermissionError, OSError) as e:
                    # 对于目录中的文件，记录错误但继续处理其他文件
                    # 可以选择跳过或记录到日志
                    print(f"警告: 无法计算文件哈希 {file_path}: {e}")
                    continue
        return result
    
    raise FileNotFoundError(f"路径既不是文件也不是目录: {path}")

