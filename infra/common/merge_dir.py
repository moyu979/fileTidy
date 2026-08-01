# CHECK: 待检查 - 共享工具 - 目录合并（补缺）
# TODO(P0): 增加文件比较功能——目前仅按路径+文件名判断是否跳过，
#           期望支持按内容比较（如文件 hash），内容不同则覆盖。

"""
目录合并工具：将源目录内容合并到目标目录，已有文件跳过、缺失的补上。
"""

import logging
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


def merge_dir(src: Path, dst: Path) -> None:
    """将 src 内容合并到 dst，已有文件跳过、缺失的补上。

    TODO(P0): 增加文件比较策略参数，当前仅按文件名判断是否已存在，
              期望支持按 hash 或 mtime 比较，不一致时覆盖。

    Args:
        src: 源目录。
        dst: 目标目录，需保证已存在。

    Raises:
        NotADirectoryError: src 或 dst 不是目录时抛出。
        FileNotFoundError: src 不存在时抛出。
        OSError: 文件操作失败时抛出。
    """
    if not src.exists():
        raise FileNotFoundError(f"源目录不存在: {src}")
    if not src.is_dir():
        raise NotADirectoryError(f"源路径不是一个目录: {src}")
    if not dst.is_dir():
        raise NotADirectoryError(f"目标路径不是一个目录: {dst}")

    for src_path in sorted(src.rglob("*")):
        rel_path = src_path.relative_to(src)
        dst_path = dst / rel_path

        if src_path.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
        elif not dst_path.exists():
            shutil.copy2(src_path, dst_path)
            logger.debug("已拷贝: %s", rel_path)
    logger.info("合并完成（已有文件已跳过）")
