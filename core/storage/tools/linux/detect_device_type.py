import re
from typing import Optional


_DISK_PATTERN = re.compile(r'^(/dev/)?(sd[a-z]+|nvme\d+n\d+)$')
_TAPE_PATTERN = re.compile(r'^(/dev/)?st\d+$')


def is_disk_path(path: Optional[str]) -> bool:
    """判断给定路径是否为磁盘设备路径。

    磁盘规则示例：/dev/sda, sdb, /dev/nvme0n1, nvme1n1
    """
    if not path:
        return False
    return _DISK_PATTERN.match(str(path)) is not None


def is_tape_path(path: Optional[str]) -> bool:
    """判断给定路径是否为磁带设备路径。

    磁带规则示例：/dev/st0, st1
    """
    if not path:
        return False
    return _TAPE_PATTERN.match(str(path)) is not None


def get_device_type(path: Optional[str]) -> Optional[str]:
    """返回设备类型："disk" | "tape"，无法识别则返回 None。"""
    if is_disk_path(path):
        return "disk"
    if is_tape_path(path):
        return "tape"
    return None


__all__ = [
    "is_disk_path",
    "is_tape_path",
    "get_device_type",
]


