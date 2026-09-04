# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - linux 平台：获取设备容量
"""linux —— 获取设备容量。"""

from ._common import _disk_info, _parse_size


def get_capacity(path: str) -> int:
    """获取设备容量（字节）。

    解析 SIZE 字段，如 "238.5G" → 字节数。

    Args:
        path: 设备路径。

    Returns:
        设备容量（字节）。
    """
    info = _disk_info(path)
    raw = info.get("size", "0")
    return _parse_size(raw)
