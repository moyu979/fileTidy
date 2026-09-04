# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - darwin 平台：获取设备序列号
"""darwin —— 获取设备序列号。"""

from ._common import _disk_info


def get_serial(path: str) -> str | None:
    """获取设备的序列号。

    从 Serial Number 字段获取，分区设备返回 None。

    Args:
        path: 设备路径。

    Returns:
        设备序列号字符串，分区设备返回 None。
    """
    info = _disk_info(path)
    # 整盘才有 Serial Number，分区没有
    if "Serial Number" in info:
        return info["Serial Number"] or None
    return None
