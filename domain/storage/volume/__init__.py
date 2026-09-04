# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - domain/storage/volume 包

"""
domain/storage/volume 包。

导入本包内任一模块都会先执行本文件，进而 eager-import 全部卷变体子类，
确保 `Volume._registry` 在 `Volume.create()` / `Volume.from_dict()` 使用前已被
`__init_subclass__` 自动填充——否则注册表为空，类型分派会静默退回基类 Volume。
"""

from domain.storage.volume.base import Volume
from domain.storage.volume.variants.ntfs import NtfsVolume
from domain.storage.volume.variants.exfat import ExfatVolume
from domain.storage.volume.variants.fat32 import Fat32Volume
from domain.storage.volume.variants.ltfs import LtfsVolume

__all__ = [
    "Volume",
    "NtfsVolume",
    "ExfatVolume",
    "Fat32Volume",
    "LtfsVolume",
]
