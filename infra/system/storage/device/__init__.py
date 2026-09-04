# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - device 系统接口门面：按 OS 转发到平台包
"""device 系统接口门面 —— 按当前 OS 转发到对应平台包。

用法（与原先模块同名，兼容现有导入）：:

    from infra.system.storage.device.get_serial import get_serial
    from infra.system.storage.device import get_capacity

平台实现位于 ``device/<platform>/``（darwin / linux / win32 / unknown），
由 ``infra.system.runtime`` 根据当前 OS 分发。
"""

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
