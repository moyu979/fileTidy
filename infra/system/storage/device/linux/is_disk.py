# CHECK: AI生成 - linux 平台：判断路径是否为磁盘
"""linux —— 判断路径是否为磁盘。"""

from ._common import _disk_info


def is_disk(path: str) -> bool:
    """判断指定路径是否为有效的磁盘设备。

    Args:
        path: 待检查的路径。

    Returns:
        True 表示是磁盘设备，False 表示不是。
    """
    try:
        _disk_info(path)
        return True
    except RuntimeError:
        return False
