# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/volume/variants/ltfs —— LtfsVolume 变体。

目的（测什么）：
- 验证 LtfsVolume 的注册与工厂分派（_type_key = "ltfs"）；
- 验证构造函数为纯透传：入参逐字段写入实例属性；
- 验证继承自 Volume 后 datas_path / meta_path 仍按挂载路径派生；
- 验证快照的 file_system 字段为 "ltfs"。

输入：
- file_system = "ltfs" 与完整卷字段（磁带卷）。

期望输出：
- 构造出 LtfsVolume 且属性与入参一致；快照 file_system 为 "ltfs"。
"""

from __future__ import annotations

import json
from datetime import datetime

from domain.storage.volume import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.variants.ltfs import LtfsVolume


def _ltfs(**overrides) -> LtfsVolume:
    """构造一个 LtfsVolume 实例。"""
    data = {
        "serial": "LT-1",
        "device_id": "DEV-LT",
        "name": "磁带卷",
        "add_time": datetime(2026, 2, 1, 12, 0, 0),
        "last_check_time": None,
        "state": VolumeState.HEALTHY,
        "capacity": 1_500_000_000_000,
        "unique_mount_point": "/mnt/ltfs",
        "file_system": "ltfs",
        "info": '{"generation": "lto9"}',
        "volume_path": "/mnt/ltfs",
    }
    data.update(overrides)
    return Volume.create(**data)  # type: ignore[return-value]


def test_ltfs_is_registered_and_dispatched():
    """输入 file_system="ltfs" → 工厂返回 LtfsVolume 且注册表登记该变体。"""
    assert LtfsVolume._type_key == "ltfs"
    assert Volume._registry["ltfs"] is LtfsVolume
    assert isinstance(_ltfs(), LtfsVolume)


def test_ltfs_constructor_passes_through_all_fields():
    """输入全部字段 → 实例属性与入参逐一一致。"""
    vol = _ltfs(name="卷LT", capacity=3, state=VolumeState.UNKNOWN)
    assert vol.serial == "LT-1"
    assert vol.device_id == "DEV-LT"
    assert vol.name == "卷LT"
    assert vol.add_time == datetime(2026, 2, 1, 12, 0, 0)
    assert vol.last_check_time is None
    assert vol.state is VolumeState.UNKNOWN
    assert vol.capacity == 3
    assert vol.unique_mount_point == "/mnt/ltfs"
    assert vol.file_system == "ltfs"
    assert vol.info == '{"generation": "lto9"}'
    assert vol.volume_path == "/mnt/ltfs"


def test_ltfs_is_a_volume():
    """输入 ltfs → 实例同时是 Volume（继承关系成立）。"""
    assert isinstance(_ltfs(), Volume)


def test_ltfs_derives_datas_and_meta_paths():
    """输入挂载路径 → datas_path / meta_path 派生为 datas、meta 子目录。"""
    vol = _ltfs(volume_path="/mnt/ltfs")
    assert vol.datas_path == "/mnt/ltfs/datas"
    assert vol.meta_path == "/mnt/ltfs/meta"


def test_ltfs_snapshot_and_json_expose_file_system():
    """输入 ltfs 卷 → 快照 file_system 为 "ltfs"，JSON 可反序列化且中文不转义。"""
    vol = _ltfs()
    snapshot = vol.to_snapshot()
    assert snapshot["file_system"] == "ltfs"
    assert snapshot["capacity"] == 1_500_000_000_000

    text = vol.to_json()
    assert "磁带卷" in text
    assert json.loads(text)["file_system"] == "ltfs"


def test_ltfs_parse_info_reads_generation():
    """输入含 generation 的 info → _parse_info 返回对应 dict。"""
    assert _ltfs()._parse_info() == {"generation": "lto9"}
