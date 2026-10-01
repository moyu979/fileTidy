# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - 仿照 hash 重构 - 系统文件 XOR 操作（配置注入 / 单双缓冲 / 向量化异或）
# NOTE: file 子系统未完成（设计未定稿），此工具仅供 file 模块使用，可能随 file 一起调整。

from __future__ import annotations

import logging
import queue
import threading

import numpy as np

from infra.common.hash import MIN_HASH_ONCE
from infra.config.interface import ConfigContentManager

logger = logging.getLogger(__name__)


class FileXor:
    """
    文件 XOR 处理器。与 ``FileHasher`` 完全对称：注入 ``hash`` 子配置
    （如 ``config["hash"]``），以下标方式读取 ``hash_once``（分块字节数）
    与 ``enable_double_buffer``（双缓冲开关），键缺失时直接抛 ``KeyError``，
    ``hash_once`` 小于 1 MiB 时抛 ``ValueError``（下限常量直接取自
    ``infra.common.hash``，不重复定义）；也可通过 ``from_params`` 直接传入这两个参数。

    计算两个文件的按位异或（b1 ^ b2，长度不等时短者按 0 补齐），
    结果写入 ``output_path``（覆盖写）。
    """

    def __init__(self, hash_config: ConfigContentManager) -> None:
        """
        初始化 FileXor。

        Args:
            hash_config: hash 子配置（由上层提取，如 ``config["hash"]``）。

        Raises:
            KeyError: ``hash_once`` / ``enable_double_buffer`` 缺失时（构造期校验）。
            ValueError: ``hash_once`` 小于 ``MIN_HASH_ONCE``（1 MiB）时。
        """
        # fail fast：构造时校验键存在与取值合法，但不保存，使用时现读（支持配置热更新）
        hash_once = int(hash_config["hash_once"])
        double_buffer = bool(hash_config["enable_double_buffer"])
        if hash_once < MIN_HASH_ONCE:
            raise ValueError(
                f"hash_once 不能小于 1 MiB（{MIN_HASH_ONCE} 字节），当前值: {hash_once}"
            )
        self._hash_config = hash_config
        logger.info(
            "FileXor constructed: hash_once=%s, double_buffer=%s",
            hash_once,
            double_buffer,
        )

    @classmethod
    def from_params(cls, hash_once: int, enable_double_buffer: bool) -> "FileXor":
        """
        免搭 AppConfig，直接传入分块参数构造。

        内部现场构造轻量 conf，走统一主构造路径。

        Args:
            hash_once: 单次读入的分块大小（字节），不得小于 ``MIN_HASH_ONCE``（1 MiB）。
            enable_double_buffer: 是否启用双缓冲（双线程）。

        Raises:
            ValueError: ``hash_once`` 小于 1 MiB 时。
        """
        return cls(_XorConfig(hash_once, enable_double_buffer))

    def compute_xor(self, file1_path: str, file2_path: str, output_path: str) -> None:
        """
        计算两个文件的按位异或（长度不等时短者按 0 补齐），结果写入输出文件。

        Args:
            file1_path: 第一个输入文件绝对路径。
            file2_path: 第二个输入文件绝对路径。
            output_path: 输出文件绝对路径（会被覆盖）。

        Raises:
            FileNotFoundError: 输入文件不存在。
            PermissionError: 没有读取或写入权限。
            OSError: 其他文件系统错误。
        """
        if self._hash_config["enable_double_buffer"]:
            return self._xor_double_buffer(file1_path, file2_path, output_path)
        return self._xor_single(file1_path, file2_path, output_path)

    def _xor_single(self, file1_path: str, file2_path: str, output_path: str) -> None:
        """
        单缓冲：一次各读一个 ``hash_once`` 块，向量化异或后写入。

        Args:
            file1_path: 第一个输入文件绝对路径。
            file2_path: 第二个输入文件绝对路径。
            output_path: 输出文件绝对路径。

        Raises:
            FileNotFoundError: 输入文件不存在。
            PermissionError: 没有读取或写入权限。
            OSError: 其他文件系统错误。
        """
        hash_once = int(self._hash_config["hash_once"])
        try:
            with open(file1_path, "rb") as f1, open(file2_path, "rb") as f2, open(output_path, "wb") as stream:
                while True:
                    b1 = f1.read(hash_once)
                    b2 = f2.read(hash_once)
                    if not b1 and not b2:
                        break
                    stream.write(self._xor_chunks(b1, b2))
        except FileNotFoundError:
            raise FileNotFoundError(f"文件不存在: {file1_path} / {file2_path} / {output_path}")
        except PermissionError:
            raise PermissionError(f"没有权限访问文件: {file1_path} / {file2_path} / {output_path}")
        except OSError as e:
            raise OSError(f"XOR 处理失败 {file1_path} / {file2_path}: {e}")

    def _xor_double_buffer(self, file1_path: str, file2_path: str, output_path: str) -> None:
        """
        双缓冲：两个读线程（各自队列）+ 一个异或写线程。

        每个读入块为 ``hash_once // 4``，两个队列容量各 2；两个文件各自
        「队列 2 块 + 读/写各 1 块在途」，峰值内存 ≤ 2 * ``hash_once``。

        与 ``FileHasher._compute_double_buffer`` 一致：异常在线程内收集，
        线程全部 join 后抛出其中第一个；任一路读线程失败即停止写出，
        不留半成品输出。

        Args:
            file1_path: 第一个输入文件绝对路径。
            file2_path: 第二个输入文件绝对路径。
            output_path: 输出文件绝对路径。

        Raises:
            FileNotFoundError: 输入文件不存在。
            PermissionError: 没有读取或写入权限。
            OSError: 其他文件系统错误。
        """
        hash_once = int(self._hash_config["hash_once"])
        chunk_size = max(1, hash_once // 4)
        q1: queue.Queue[bytes | None] = queue.Queue(maxsize=2)
        q2: queue.Queue[bytes | None] = queue.Queue(maxsize=2)
        sentinel = None
        errors: list[BaseException] = []
        errors_lock = threading.Lock()

        def reader(src_path: str, q: queue.Queue[bytes | None]) -> None:
            try:
                with open(src_path, "rb") as f:
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

        def xor_writer(fout) -> None:
            # done1/done2 记录各自源是否已结束：一旦取到 sentinel 即置位，
            # 之后不再对该队列 get（否则较短的源结束后会永久阻塞等待空队列）
            done1 = done2 = False

            def drain(q: queue.Queue[bytes | None]) -> None:
                # 丢弃剩余数据直到 sentinel，保证读线程 put 不阻塞
                while q.get() is not sentinel:
                    pass

            while True:
                b1 = b2 = b""
                if not done1:
                    data = q1.get()
                    if data is sentinel:
                        done1 = True
                    else:
                        b1 = data
                if not done2:
                    data = q2.get()
                    if data is sentinel:
                        done2 = True
                    else:
                        b2 = data
                if done1 and done2:
                    break
                with errors_lock:
                    failed = bool(errors)
                if failed:
                    # 任一路读线程已失败 → 停止写出（不留零补齐的半成品），排空队列
                    if not done1:
                        drain(q1)
                    if not done2:
                        drain(q2)
                    break
                try:
                    fout.write(self._xor_chunks(b1, b2))
                except Exception as exc:
                    with errors_lock:
                        errors.append(exc)
                    if not done1:
                        drain(q1)
                    if not done2:
                        drain(q2)
                    break

        t_reader1 = threading.Thread(target=reader, args=(file1_path, q1), name="xor-reader-1")
        t_reader2 = threading.Thread(target=reader, args=(file2_path, q2), name="xor-reader-2")

        with open(output_path, "wb") as fout:
            t_writer = threading.Thread(target=xor_writer, args=(fout,), name="xor-writer")
            t_reader1.start()
            t_reader2.start()
            t_writer.start()

            t_reader1.join()
            t_reader2.join()
            t_writer.join()

        if errors:
            raise errors[0]

    @staticmethod
    def _xor_chunks(b1: bytes, b2: bytes) -> bytes:
        """对齐长度后向量化异或，返回结果字节串（短者按 0 补齐）。"""
        # 补齐长度
        if len(b1) < len(b2):
            b1 += b"\x00" * (len(b2) - len(b1))
        elif len(b2) < len(b1):
            b2 += b"\x00" * (len(b1) - len(b2))

        # 转为 NumPy 数组（uint8）并向量化异或
        arr1 = np.frombuffer(b1, dtype=np.uint8)
        arr2 = np.frombuffer(b2, dtype=np.uint8)
        return np.bitwise_xor(arr1, arr2).tobytes()


class _XorConfig:
    """
    轻量 hash 子配置：实现与 ``SingleFileConfig`` 一致的下标读取接口，
    供 ``FileXor.from_params`` 内部现场构造。
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
            raise KeyError(f"缺少配置项 {key!r}（_XorConfig）") from None
