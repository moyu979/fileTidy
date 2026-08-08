# CHECK: ai生成，待检查 - domain/storage/device 包

"""
domain/storage/device 包。

导入本包内任一模块都会先执行本文件，进而 eager-import 全部设备变体子类，
确保 `Device._registry` 在 `Device.create()` / `Device.from_dict()` 使用前已被
`__init_subclass__` 自动填充——否则注册表为空，类型分派会静默退回基类 Device。
"""

from domain.storage.device.base import Device
from domain.storage.device.variants.HDD import HddDevice
from domain.storage.device.variants.SSD import SsdDevice
from domain.storage.device.variants.Tape import TapeDevice
from domain.storage.device.variants.TfSd import TfSdCardDevice

__all__ = [
    "Device",
    "HddDevice",
    "SsdDevice",
    "TapeDevice",
    "TfSdCardDevice",
]
