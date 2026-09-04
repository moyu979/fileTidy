# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - darwin 平台：判断路径是否为磁盘
"""darwin —— 判断路径是否为磁盘。"""

import subprocess

from ._common import _disk_info


def is_disk(path: str) -> bool:
    """判断路径是否可被 diskutil 识别为磁盘。

    Args:
        path: 待检查的路径。

    Returns:
        True 表示是磁盘设备，False 表示不是。
    """
    try:
        _disk_info(path)
        return True
    except (RuntimeError, subprocess.TimeoutExpired):
        return False
