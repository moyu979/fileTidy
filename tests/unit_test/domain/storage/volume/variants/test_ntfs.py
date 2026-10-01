# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/volume/variants/ntfs —— NtfsVolume 变体。

目的（测什么）：
- 验证 NtfsVolume 的注册与工厂分派（_type_key = "ntfs"）；
- 验证构造函数为纯透传：入参逐字段写入实例属性；
- 验证继承自 Volume 后 datas_path / meta_path 仍按挂载路径派生；
- 验证快照的 file_system 字段为 "ntfs"。

输入：
- file_system = "ntfs" 与完整卷字段。

期望输出：
- 构造出 NtfsVolume 且属性与入参一致；快照 file_system 为 "ntfs"。
"""

from __future__ import annotations

import json
from datetime import datetime

from domain.storage.volume import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.variants.ntfs import NtfsVolume


def _ntfs(**overrides) -> NtfsVolume:
    """构造一个 NtfsVolume 实例。"""
    data = {
        "serial": "NT-1",
        "device_id": "DEV-NT",
        "name": "数据卷",
        "add_time": datetime(2026, 2, 1, 12, 0, 0),
        "last_check_time": None,
        "state": VolumeState.HEALTHY,
        "capacity": 2_000_000_000_000,
        "unique_mount_point": "/mnt/vol",
        "file_system": "ntfs",
        "info": "{}",
        "volume_path": "/mnt/vol",
    }
    data.update(overrides)
    return Volume.create(**data)  # type: ignore[return-value]


def test_ntfs_is_registered_and_dispatched():
    """输入 file_system="ntfs" → 工厂返回 NtfsVolume 且注册表登记该变体。"""
    assert NtfsVolume._type_key == "ntfs"
    assert Volume._registry["ntfs"] is NtfsVolume
    assert isinstance(_ntfs(), NtfsVolume)


def test_ntfs_constructor_passes_through_all_fields():
    """输入全部字段 → 实例属性与入参逐一一致。"""
    vol = _ntfs(name="卷NT", capacity=11, state=VolumeState.FAULT)
    assert vol.serial == "NT-1"
    assert vol.device_id == "DEV-NT"
    assert vol.name == "卷NT"
    assert vol.add_time == datetime(2026, 2, 1, 12, 0, 0)
    assert vol.last_check_time is None
    assert vol.state is VolumeState.FAULT
    assert vol.capacity == 11
    assert vol.unique_mount_point == "/mnt/vol"
    assert vol.file_system == "ntfs"
    assert vol.volume_path == "/mnt/vol"


def test_ntfs_is_a_volume():
    """输入 ntfs → 实例同时是 Volume（继承关系成立）。"""
    assert isinstance(_ntfs(), Volume)


def test_ntfs_derives_datas_and_meta_paths():
    """输入挂载路径 → datas_path / meta_path 派生为 datas、meta 子目录。"""
    vol = _ntfs(volume_path="/mnt/vol")
    assert vol.datas_path == "/mnt/vol/datas"
    assert vol.meta_path == "/mnt/vol/meta"


def test_ntfs_datas_and_meta_are_none_without_volume_path():
    """输入 volume_path=None → datas_path / meta_path 均为 None。"""
    vol = _ntfs(volume_path=None)
    assert vol.datas_path is None
    assert vol.meta_path is None


def test_ntfs_snapshot_and_json_expose_file_system():
    """输入 ntfs 卷 → 快照 file_system 为 "ntfs"，JSON 可反序列化且中文不转义。"""
    vol = _ntfs()
    snapshot = vol.to_snapshot()
    assert snapshot["file_system"] == "ntfs"
    assert snapshot["state"] is VolumeState.HEALTHY

    text = vol.to_json()
    assert "数据卷" in text
    assert json.loads(text)["file_system"] == "ntfs"
    assert json.loads(text)["state"] == "healthy"
