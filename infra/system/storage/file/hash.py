import hashlib
import os
import queue
from typing import List
import threading
from typing import Optional

from apps.common.config.config import config_manager


def get_md5(path: str) -> str:
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

def get_sha512(
    file_path: str,
    *,
    max_mem_bytes: int = None,  # 512MB
    chunk_num: int = 8,       # 8MB
    use_threads: bool = False,
) -> str:
    """
    计算文件的 SHA-512 摘要，支持单线程 / 双线程，
    并显式限制最大内存占用。

    参数:
        file_path: 文件路径
        max_mem_bytes: 最大文件相关内存占用
        chunk_size: 每块读取大小
        use_threads: 是否启用双线程（读 / hash）

    返回:
        SHA-512 hex digest
    """
    if not max_mem_bytes:
        max_mem_bytes = int(config_manager.get("hash_check_memery")) * 1024 * 1024
    
    if chunk_num <= 0:
        raise ValueError("chunk_size must be > 0")


    h = hashlib.sha512()

    # -------- 单线程路径 --------
    if not use_threads:
        with open(file_path, "rb") as f:
            while True:
                data = f.read(max_mem_bytes)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()

    # -------- 双线程路径 --------
    chunk_size = max_mem_bytes // chunk_num # 这里后面改一下，要按整兆走
    max_queue_items = chunk_num
    q: queue.Queue[Optional[bytes]] = queue.Queue(maxsize=max_queue_items)

    sentinel = None  # 结束标记

    def reader():
        try:
            with open(file_path, "rb") as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    q.put(data)  # 阻塞直到 hash 线程消费
        finally:
            q.put(sentinel)

    def hasher():
        while True:
            data = q.get()
            if data is sentinel:
                break
            h.update(data)
            q.task_done()

    t_reader = threading.Thread(target=reader, name="sha512-reader")
    t_hasher = threading.Thread(target=hasher, name="sha512-hasher")

    t_reader.start()
    t_hasher.start()

    t_reader.join()
    t_hasher.join()

    return h.hexdigest()


def compute_hash(path: str, enable_sha512: bool = True, enable_md5: bool = True) -> dict:
    """
    计算文件的哈希值，支持同时计算多个哈希算法
    
    Args:
        path: 需要计算哈希的文件路径
        enable_sha512: 是否启用SHA512计算
        enable_md5: 是否启用MD5计算
        
    Returns:
        dict: 包含计算结果的字典，key为"sha512"或"md5"，value为对应的哈希值
              只包含启用的哈希算法的结果
        
    Raises:
        FileNotFoundError: 文件不存在
        PermissionError: 没有读取权限
        OSError: 其他文件系统错误
        ValueError: 至少需要启用一个哈希算法
    """
    if not enable_sha512 and not enable_md5:
        raise ValueError("至少需要启用一个哈希算法（sha512或md5）")
    
    # 获取分块大小
    try:
        chunk_size = int(config_manager.get("hash_once")) * 1024 * 1024
    except (ValueError):
        # 默认值：512M
        chunk_size = 512 * 1024 * 1024
    
    # 初始化需要的哈希器
    hashers = {}
    if enable_sha512:
        hashers["sha512"] = hashlib.sha512()
    if enable_md5:
        hashers["md5"] = hashlib.md5()
    
    # 分块读取并更新所有启用的哈希器
    try:
        with open(path, "rb") as stream:
            for chunk in iter(lambda: stream.read(chunk_size), b""):
                for hasher in hashers.values():
                    hasher.update(chunk)
    except FileNotFoundError:
        raise FileNotFoundError(f"文件不存在: {path}")
    except PermissionError:
        raise PermissionError(f"没有权限读取文件: {path}")
    except OSError as e:
        raise OSError(f"读取文件失败 {path}: {e}")
    
    # 返回结果字典
    result = {}
    if enable_sha512:
        result["sha512"] = hashers["sha512"].hexdigest()
    if enable_md5:
        result["md5"] = hashers["md5"].hexdigest()
    
    return result


def get_hash(path: str,method="sha512") -> List[List[str]]:
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
    
    _hash_func = sha512_file if method == "sha512" else _md5_file

    if os.path.isfile(path):
        try:
            return [[path, _hash_func(path)]]
        except (PermissionError, OSError) as e:
            # 对于单个文件，直接抛出异常
            raise
    
    if os.path.isdir(path):
        result = []
        for root, _, files in os.walk(path):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    result.append([file_path, _hash_func(file_path)])
                except (PermissionError, OSError) as e:
                    # 对于目录中的文件，记录错误但继续处理其他文件
                    # 可以选择跳过或记录到日志
                    print(f"警告: 无法计算文件哈希 {file_path}: {e}")
                    continue
        return result
    
    raise FileNotFoundError(f"路径既不是文件也不是目录: {path}")

