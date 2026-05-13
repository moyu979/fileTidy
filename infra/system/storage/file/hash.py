from __future__ import annotations

import hashlib
import os
import queue
import threading
from typing import Optional

from infra.config.config import Config


class file_hash:
    """
    文件哈希工具类。构造时注入 ``Config``（通常取 ``base`` 段中的
    ``hash_check_memery`` / ``hash_once`` 等键）；未注入则使用内置默认分块大小。
    """

    def __init__(self, config: Config | None = None) -> None:
        self._config = config

    def _base_section(self) -> dict:
        if self._config is None:
            return {}
        raw = self._config.get("base")
        return raw if isinstance(raw, dict) else {}

    def _int_mb(self, key: str, default_mb: int) -> int:
        raw = self._base_section().get(key)
        if raw is None:
            return default_mb
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default_mb

    def _chunk_size_bytes_hash_check(self) -> int:
        return self._int_mb("hash_check_memery", 512) * 1024 * 1024

    def _chunk_size_bytes_hash_once(self) -> int:
        return self._int_mb("hash_once", 512) * 1024 * 1024

    def get_md5(self, path: str) -> str:
        """
        计算文件的 MD5 哈希值。

        Args:
            path: 文件路径

        Returns:
            MD5 十六进制字符串

        Raises:
            FileNotFoundError: 文件不存在
            PermissionError: 没有读取权限
            OSError: 其他文件系统错误
        """
        chunk_size = self._chunk_size_bytes_hash_check()
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
        self,
        file_path: str,
        *,
        max_mem_bytes: int | None = None,
        chunk_num: int = 8,
        use_threads: bool = False,
    ) -> str:
        """
        计算文件的 SHA-512 摘要，支持单线程 / 双线程，并显式限制最大内存占用。

        参数:
            file_path: 文件路径
            max_mem_bytes: 最大文件相关内存占用（未指定时从配置 ``hash_check_memery`` 读取）
            chunk_num: 双线程模式下队列块数相关参数
            use_threads: 是否启用双线程（读 / hash）

        返回:
            SHA-512 hex digest
        """
        if not max_mem_bytes:
            max_mem_bytes = self._chunk_size_bytes_hash_check()

        if chunk_num <= 0:
            raise ValueError("chunk_size must be > 0")

        h = hashlib.sha512()

        if not use_threads:
            with open(file_path, "rb") as f:
                while True:
                    data = f.read(max_mem_bytes)
                    if not data:
                        break
                    h.update(data)
            return h.hexdigest()

        chunk_size = max_mem_bytes // chunk_num
        max_queue_items = chunk_num
        q: queue.Queue[Optional[bytes]] = queue.Queue(maxsize=max_queue_items)

        sentinel = None

        def reader() -> None:
            try:
                with open(file_path, "rb") as f:
                    while True:
                        data = f.read(chunk_size)
                        if not data:
                            break
                        q.put(data)
            finally:
                q.put(sentinel)

        def hasher() -> None:
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

    def compute_hash(
        self, path: str, enable_sha512: bool = True, enable_md5: bool = True
    ) -> dict:
        """
        计算文件的哈希值，支持同时计算多个哈希算法。

        Args:
            path: 需要计算哈希的文件路径
            enable_sha512: 是否启用 SHA512 计算
            enable_md5: 是否启用 MD5 计算

        Returns:
            字典，键为 ``sha512`` / ``md5``，值为对应哈希值

        Raises:
            FileNotFoundError: 文件不存在
            PermissionError: 没有读取权限
            OSError: 其他文件系统错误
            ValueError: 至少需要启用一个哈希算法
        """
        if not enable_sha512 and not enable_md5:
            raise ValueError("至少需要启用一个哈希算法（sha512或md5）")

        chunk_size = self._chunk_size_bytes_hash_once()

        hashers = {}
        if enable_sha512:
            hashers["sha512"] = hashlib.sha512()
        if enable_md5:
            hashers["md5"] = hashlib.md5()

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

        result: dict[str, str] = {}
        if enable_sha512:
            result["sha512"] = hashers["sha512"].hexdigest()
        if enable_md5:
            result["md5"] = hashers["md5"].hexdigest()

        return result

    def get_hash(self, path: str, method: str = "sha512") -> list[list[str]]:
        """
        获取文件或目录中所有文件的哈希值。

        Args:
            path: 文件或目录路径
            method: ``sha512`` 或 ``md5``

        Returns:
            ``[[path, hash], ...]``

        Raises:
            FileNotFoundError: 路径不存在
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"路径不存在: {path}")

        _hash_func = self.get_sha512 if method == "sha512" else self.get_md5

        if os.path.isfile(path):
            return [[path, _hash_func(path)]]

        if os.path.isdir(path):
            result: list[list[str]] = []
            for root, _, files in os.walk(path):
                for name in files:
                    file_path = os.path.join(root, name)
                    try:
                        result.append([file_path, _hash_func(file_path)])
                    except (PermissionError, OSError) as e:
                        print(f"警告: 无法计算文件哈希 {file_path}: {e}")
                        continue
            return result

        raise FileNotFoundError(f"路径既不是文件也不是目录: {path}")
