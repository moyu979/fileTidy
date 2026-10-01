# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/volume/variants/fat32 —— Fat32Volume 变体。

目的（测什么）：
- 验证 Fat32Volume 的注册与工厂分派（_type_key = "fat32"）；
- 验证构造函数为纯透传：入参逐字段写入实例属性；
- 验证继承自 Volume 后 datas_path / meta_path 仍按挂载路径派生；
- 验证快照的 file_system 字段为 "fat32"。

输入：
- file_system = "fat32" 与完整卷字段。

期望输出：
- 构造出 Fat32Volume 且属性与入参一致；快照 file_system 为 "fat32"。
"""

from __future__ import annotations

import json
from datetime import datetime

from domain.storage.volume import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.variants.fat32 import Fat32Volume


def _fat32(**overrides) -> Fat32Volume:
    """构造一个 Fat32Volume 实例。"""
    data = {
        "serial": "FA-1",
        "device_id": "DEV-FA",
        "name": "fat32卷",
        "add_time": datetime(2026, 2, 1, 12, 0, 0),
        "last_check_time": None,
        "state": VolumeState.HEALTHY,
        "capacity": 32_000_000_000,
        "unique_mount_point": "/mnt/fa",
        "file_system": "fat32",
        "info": "{}",
        "volume_path": "/mnt/fa",
    }
    data.update(overrides)
    return Volume.create(**data)  # type: ignore[return-value]


def test_fat32_is_registered_and_dispatched():
    """输入 file_system="fat32" → 工厂返回 Fat32Volume 且注册表登记该变体。"""
    assert Fat32Volume._type_key == "fat32"
    assert Volume._registry["fat32"] is Fat32Volume
    assert isinstance(_fat32(), Fat32Volume)


def test_fat32_constructor_passes_through_all_fields():
    """输入全部字段 → 实例属性与入参逐一一致。"""
    vol = _fat32(name="卷FA", capacity=9, state=VolumeState.REMOVED)
    assert vol.serial == "FA-1"
    assert vol.device_id == "DEV-FA"
    assert vol.name == "卷FA"
    assert vol.add_time == datetime(2026, 2, 1, 12, 0, 0)
    assert vol.last_check_time is None
    assert vol.state is VolumeState.REMOVED
    assert vol.capacity == 9
    assert vol.unique_mount_point == "/mnt/fa"
    assert vol.file_system == "fat32"
    assert vol.volume_path == "/mnt/fa"


def test_fat32_is_a_volume():
    """输入 fat32 → 实例同时是 Volume（继承关系成立）。"""
    assert isinstance(_fat32(), Volume)


def test_fat32_derives_datas_and_meta_paths():
    """输入挂载路径 → datas_path / meta_path 派生为 datas、meta 子目录。"""
    vol = _fat32(volume_path="/mnt/fa")
    assert vol.datas_path == "/mnt/fa/datas"
    assert vol.meta_path == "/mnt/fa/meta"


def test_fat32_snapshot_and_json_expose_file_system():
    """输入 fat32 卷 → 快照 file_system 为 "fat32"，JSON 可反序列化且中文不转义。"""
    vol = _fat32()
    snapshot = vol.to_snapshot()
    assert snapshot["file_system"] == "fat32"
    assert snapshot["unique_mount_point"] == "/mnt/fa"

    text = vol.to_json()
    assert "fat32卷" in text
    assert json.loads(text)["file_system"] == "fat32"
