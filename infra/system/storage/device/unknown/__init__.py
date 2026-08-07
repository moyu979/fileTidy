# CHECK: AI生成 - unknown 平台包：未知 OS 回退占位实现（手动输入）
"""unknown 平台包 —— 未知 OS 回退的占位实现（手动输入）。"""

from .get_serial import get_serial
from .get_path import get_path
from .get_capacity import get_capacity
from .get_type import get_type
from .get_healthy import get_healthy
from .is_disk import is_disk

__all__ = [
    "get_serial",
    "get_path",
    "get_capacity",
    "get_type",
    "get_healthy",
    "is_disk",
]
