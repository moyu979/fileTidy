# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/volume/variants/exfat —— ExfatVolume 变体。

目的（测什么）：
- 验证 ExfatVolume 的注册与工厂分派（_type_key = "exfat"）；
- 验证构造函数为纯透传：入参逐字段写入实例属性；
- 验证继承自 Volume 后 datas_path / meta_path 仍按挂载路径派生；
- 验证快照的 file_system 字段为 "exfat"。

输入：
- file_system = "exfat" 与完整卷字段。

期望输出：
- 构造出 ExfatVolume 且属性与入参一致；快照 file_system 为 "exfat"。
"""

from __future__ import annotations

import json
from datetime import datetime

from domain.storage.volume import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.variants.exfat import ExfatVolume


def _exfat(**overrides) -> ExfatVolume:
    """构造一个 ExfatVolume 实例。"""
    data = {
        "serial": "EX-1",
        "device_id": "DEV-EX",
        "name": "exfat卷",
        "add_time": datetime(2026, 2, 1, 12, 0, 0),
        "last_check_time": None,
        "state": VolumeState.HEALTHY,
        "capacity": 64_000_000_000,
        "unique_mount_point": "/mnt/ex",
        "file_system": "exfat",
        "info": '{"cluster": 128}',
        "volume_path": "/mnt/ex",
    }
    data.update(overrides)
    return Volume.create(**data)  # type: ignore[return-value]


def test_exfat_is_registered_and_dispatched():
    """输入 file_system="exfat" → 工厂返回 ExfatVolume 且注册表登记该变体。"""
    assert ExfatVolume._type_key == "exfat"
    assert Volume._registry["exfat"] is ExfatVolume
    assert isinstance(_exfat(), ExfatVolume)


def test_exfat_constructor_passes_through_all_fields():
    """输入全部字段 → 实例属性与入参逐一一致。"""
    vol = _exfat(name="卷EX", capacity=7, state=VolumeState.DANGER)
    assert vol.serial == "EX-1"
    assert vol.device_id == "DEV-EX"
    assert vol.name == "卷EX"
    assert vol.add_time == datetime(2026, 2, 1, 12, 0, 0)
    assert vol.last_check_time is None
    assert vol.state is VolumeState.DANGER
    assert vol.capacity == 7
    assert vol.unique_mount_point == "/mnt/ex"
    assert vol.file_system == "exfat"
    assert vol.info == '{"cluster": 128}'
    assert vol.volume_path == "/mnt/ex"


def test_exfat_is_a_volume():
    """输入 exfat → 实例同时是 Volume（继承关系成立）。"""
    assert isinstance(_exfat(), Volume)


def test_exfat_derives_datas_and_meta_paths():
    """输入挂载路径 → datas_path / meta_path 派生为 datas、meta 子目录。"""
    vol = _exfat(volume_path="/mnt/ex")
    assert vol.datas_path == "/mnt/ex/datas"
    assert vol.meta_path == "/mnt/ex/meta"


def test_exfat_snapshot_and_json_expose_file_system():
    """输入 exfat 卷 → 快照 file_system 为 "exfat"，JSON 可反序列化且中文不转义。"""
    vol = _exfat()
    snapshot = vol.to_snapshot()
    assert snapshot["file_system"] == "exfat"
    assert snapshot["volume_path"] == "/mnt/ex"

    text = vol.to_json()
    assert "exfat卷" in text
    assert json.loads(text)["file_system"] == "exfat"
