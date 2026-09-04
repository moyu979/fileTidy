# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - darwin 平台：获取设备容量
"""darwin —— 获取设备容量。"""

import re

from ._common import _disk_info


def get_capacity(path: str) -> int:
    """获取设备容量（字节）。

    解析 Disk Size 行括号内的字节数。

    Args:
        path: 设备路径。

    Returns:
        设备容量（字节）。

    Raises:
        ValueError: 无法解析容量时抛出。
    """
    info = _disk_info(path)
    raw = info.get("Disk Size", "")
    match = re.search(r"\((\d+)\s+Bytes\)", raw)
    if match:
        return int(match.group(1))
    raise ValueError(f"无法解析容量: {path}")
