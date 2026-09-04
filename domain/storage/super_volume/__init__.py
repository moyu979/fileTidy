# CHECK: 待检查 - domain/storage/super_volume 包

"""
domain/storage/super_volume 包。

导入本包内任一模块都会先执行本文件，进而 eager-import 全部超级卷变体子类，
确保 `SuperVolume._registry` 在 `SuperVolume.create()` / `SuperVolume.from_dict()`
使用前已被 `__init_subclass__` 自动填充——否则注册表为空，类型分派会静默退回
基类 SuperVolume。
"""

from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.variants.copy import CopySuperVolume
from domain.storage.super_volume.variants.snapraid_raid5 import SnapraidRaid5SuperVolume

__all__ = [
    "SuperVolume",
    "CopySuperVolume",
    "SnapraidRaid5SuperVolume",
]
