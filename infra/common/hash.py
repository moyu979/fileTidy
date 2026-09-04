# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 系统文件哈希计算 - 文件完整性校验
# NOTE: file 子系统未完成（设计未定稿），此工具仅供 file 模块使用，可能随 file 一起调整。

from __future__ import annotations

import hashlib
import logging
import queue
import threading

from infra.config.interface import ConfigContentManager

logger = logging.getLogger(__name__)


class FileHasher:
    """
    文件哈希工具类。注入 ``hash`` 子配置（如 ``config["hash"]``），
    以下标方式读取 ``hash_once``（分块字节数）与 ``enable_double_buffer``（双缓冲开关），
    键缺失时直接抛 ``KeyError``；也可通过 ``from_params`` 直接传入这两个参数。
    """

    def __init__(self, hash_config: ConfigContentManager) -> None:
        """
        初始化 FileHasher。

        Args:
            hash_config: hash 子配置（由上层提取，如 ``config["hash"]``）。

        Raises:
            KeyError: ``hash_once`` / ``enable_double_buffer`` 缺失时（构造期校验）。
        """
        # fail fast：构造时校验键存在，但不保存，使用时现读（支持配置热更新）
        hash_once = int(hash_config["hash_once"])
        double_buffer = bool(hash_config["enable_double_buffer"])
        self._hash_config = hash_config
        logger.info(
            "FileHasher constructed: hash_once=%s, double_buffer=%s",
            hash_once,
            double_buffer,
        )

    @classmethod
    def from_params(cls, hash_once: int, enable_double_buffer: bool) -> "FileHasher":
        """
        免搭 AppConfig，直接传入哈希参数构造。

        内部现场构造轻量 conf，走统一主构造路径。

        Args:
            hash_once: 单次读入的分块大小（字节）。
            enable_double_buffer: 是否启用双缓冲（双线程）。
        """
        return cls(_HashConfig(hash_once, enable_double_buffer))

    def compute_hash(self, path: str) -> dict[str, str]:
        """
        计算文件的 MD5 与 SHA-512，同时返回。

        Args:
            path: 文件绝对路径。

        Returns:
            ``{"sha512": ..., "md5": ...}``

        Raises:
            FileNotFoundError: 文件不存在
            PermissionError: 没有读取权限
            OSError: 其他文件系统错误
        """
        if self._hash_config["enable_double_buffer"]:
            return self._compute_double_buffer(path)
        return self._compute_single(path)

    def _compute_single(self, path: str) -> dict[str, str]:
        """
        单缓冲：一次读一个 ``hash_once`` 块，同时更新 MD5 与 SHA-512。

        Args:
            path: 文件绝对路径。

        Returns:
            ``{"sha512": ..., "md5": ...}``
        """
        hash_once = int(self._hash_config["hash_once"])
        md5 = hashlib.md5()
        sha512 = hashlib.sha512()
        try:
            with open(path, "rb") as stream:
                while True:
                    chunk = stream.read(hash_once)
                    if not chunk:
                        break
                    md5.update(chunk)
                    sha512.update(chunk)
        except FileNotFoundError:
            raise FileNotFoundError(f"文件不存在: {path}")
        except PermissionError:
            raise PermissionError(f"没有权限读取文件: {path}")
        except OSError as e:
            raise OSError(f"读取文件失败 {path}: {e}")
        return {"sha512": sha512.hexdigest(), "md5": md5.hexdigest()}

    def _compute_double_buffer(self, path: str) -> dict[str, str]:
        """
        双缓冲：读线程 + 哈希线程。

        每个读入块为 ``hash_once // 4``，队列容量 2；队列 2 块 + hasher/reader 各 1 块在途，
        峰值内存 ≤ ``hash_once``。

        Args:
            path: 文件绝对路径。

        Returns:
            ``{"sha512": ..., "md5": ...}``
        """
        hash_once = int(self._hash_config["hash_once"])
        chunk_size = max(1, hash_once // 4)
        q: queue.Queue[bytes | None] = queue.Queue(maxsize=2)
        sentinel = None
        errors: list[BaseException] = []
        errors_lock = threading.Lock()

        md5 = hashlib.md5()
        sha512 = hashlib.sha512()

        def reader() -> None:
            try:
                with open(path, "rb") as f:
                    while True:
                        data = f.read(chunk_size)
                        if not data:
                            break
                        q.put(data)
            except Exception as exc:
                # 收集读线程异常（如文件不存在/无权限），避免异常被线程吞掉
                with errors_lock:
                    errors.append(exc)
            finally:
                q.put(sentinel)

        def hasher() -> None:
            while True:
                data = q.get()
                if data is sentinel:
                    break
                md5.update(data)
                sha512.update(data)

        t_reader = threading.Thread(target=reader, name="hash-reader")
        t_hasher = threading.Thread(target=hasher, name="hash-hasher")

        t_reader.start()
        t_hasher.start()

        t_reader.join()
        t_hasher.join()

        if errors:
            raise errors[0]

        return {"sha512": sha512.hexdigest(), "md5": md5.hexdigest()}


class _HashConfig:
    """
    轻量 hash 子配置：实现与 ``SingleFileConfig`` 一致的下标读取接口，
    供 ``FileHasher.from_params`` 内部现场构造。
    """

    def __init__(self, hash_once: int, enable_double_buffer: bool) -> None:
        self._values = {
            "hash_once": int(hash_once),
            "enable_double_buffer": bool(enable_double_buffer),
        }

    def get(self, key: str, default: object = None) -> object:
        return self._values.get(key, default)

    def __getitem__(self, key: str) -> object:
        try:
            return self._values[key]
        except KeyError:
            raise KeyError(f"缺少配置项 {key!r}（_HashConfig）") from None
