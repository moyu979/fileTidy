# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - darwin 平台包：macOS 设备操作实现
"""darwin 平台包 —— macOS (Darwin 内核) 设备操作实现。"""

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
