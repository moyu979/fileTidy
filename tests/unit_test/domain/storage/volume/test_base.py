# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/volume/base —— Volume 实体基类。

目的（测什么）：
- 验证 Volume._resolve / Volume.create 按 file_system 的工厂分派
  （含 None 与未注册文件系统回退基类、子类声明 _type_key 后自动注册）；
- 验证 serial 必填校验、create 默认值填充与显式字段透传；
- 验证 from_dict 重建、volume_path 覆盖、to_snapshot 字段集合与 to_json 序列化；
- 验证 datas_path / meta_path 路径派生（含 volume_path 为 None 的兜底）；
- 验证 _parse_info 对空 / 非法 / 非对象 JSON 的兜底。

输入：
- file_system 字符串（"ntfs" / "exfat" / "fat32" / "ltfs" / None / 未注册的 "ext4"）；
- 卷字段字典（完整字段、只含 serial、缺 serial）；
- volume_path（"/mnt/vol" / None）；
- info 字符串（None / "" / "not-json" / "[1, 2]" / 合法对象 JSON）。

期望输出：
- 对应变体实例；serial 为空时 ValueError；未知文件系统回退 Volume 基类；
- 快照含全部 11 个字段、JSON 可反序列化且中文不转义；
- datas_path / meta_path 为 <volume_path>/datas、<volume_path>/meta，无路径时为 None；
- 非法 info 一律解析为 {}，合法对象 JSON 解析为对应 dict。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

# 导入包即触发变体注册，保证工厂分派可用
from domain.storage.volume import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.variants.exfat import ExfatVolume
from domain.storage.volume.variants.fat32 import Fat32Volume
from domain.storage.volume.variants.ltfs import LtfsVolume
from domain.storage.volume.variants.ntfs import NtfsVolume

SNAPSHOT_KEYS = {
    "serial", "device_id", "name", "add_time", "last_check_time", "state",
    "capacity", "unique_mount_point", "file_system", "info", "volume_path",
}


def _volume(file_system: str | None = None, **overrides) -> Volume:
    """构造一个 Volume 实例，未显式给出的字段使用固定测试值。"""
    data = {
        "serial": "VOL-1",
        "device_id": "DEV-1",
        "name": "数据卷",
        "add_time": datetime(2026, 2, 1, 12, 0, 0),
        "last_check_time": None,
        "state": VolumeState.HEALTHY,
        "capacity": 2_000_000_000_000,
        "unique_mount_point": "/mnt/vol",
        "file_system": file_system,
        "info": "{}",
        "volume_path": "/mnt/vol",
    }
    data.update(overrides)
    return Volume.create(**data)


@pytest.mark.parametrize(
    ("file_system", "expected"),
    [
        ("ntfs", NtfsVolume),
        ("exfat", ExfatVolume),
        ("fat32", Fat32Volume),
        ("ltfs", LtfsVolume),
        (None, Volume),
        ("ext4", Volume),
    ],
)
def test_create_dispatches_by_file_system(file_system, expected):
    """输入 file_system（已注册 / None / 未注册）→ 返回对应变体类，未注册回退基类。"""
    assert isinstance(_volume(file_system), expected)


def test_resolve_returns_registered_variant_class():
    """输入已注册文件系统 → _resolve 返回注册表中的变体类本身。"""
    assert Volume._resolve("ntfs") is NtfsVolume
    assert Volume._resolve("ltfs") is LtfsVolume


def test_resolve_falls_back_to_base_class():
    """输入 None 或未注册文件系统 → _resolve 返回 Volume 基类本身。"""
    assert Volume._resolve(None) is Volume
    assert Volume._resolve("ext4") is Volume


def test_registry_contains_builtin_variants():
    """导入包后 → 注册表包含 4 个内置文件系统变体且指向对应类。"""
    assert {"ntfs", "exfat", "fat32", "ltfs"} <= set(Volume._registry)
    assert Volume._registry["exfat"] is ExfatVolume
    assert Volume._registry["fat32"] is Fat32Volume


def test_subclass_without_type_key_is_not_registered():
    """定义未声明 _type_key 的子类 → 不进入注册表，_resolve 仍回退基类。"""
    class _AnonymousVolume(Volume):
        """未声明 _type_key 的临时子类。"""

    assert "anonymous_volume" not in Volume._registry
    assert Volume._resolve("anonymous_volume") is Volume


def test_create_requires_serial():
    """输入空 serial → ValueError。"""
    with pytest.raises(ValueError, match="serial"):
        Volume.create(serial="")


def test_from_dict_without_serial_raises():
    """输入缺 serial 的字典 → ValueError（由 create 统一校验）。"""
    with pytest.raises(ValueError, match="serial"):
        Volume.from_dict({"name": "无序列号"})


def test_create_fills_defaults():
    """只传 serial → 其余字段取默认值（空串 / None）。"""
    vol = Volume.create(serial="VOL-1")
    assert vol.serial == "VOL-1"
    assert vol.device_id == ""
    assert vol.name == ""
    assert vol.add_time is None
    assert vol.last_check_time is None
    assert vol.state is None
    assert vol.capacity is None
    assert vol.unique_mount_point is None
    assert vol.file_system is None
    assert vol.info is None
    assert vol.volume_path is None
    assert type(vol) is Volume


def test_create_keeps_explicit_fields():
    """传入全部字段 → 实例属性与入参一致，且类型为 ntfs 变体。"""
    vol = _volume("ntfs", name="卷A", capacity=123, state=VolumeState.DANGER)
    assert isinstance(vol, NtfsVolume)
    assert (vol.name, vol.file_system, vol.capacity) == ("卷A", "ntfs", 123)
    assert vol.state is VolumeState.DANGER
    assert vol.device_id == "DEV-1"
    assert vol.unique_mount_point == "/mnt/vol"


def test_from_dict_roundtrip_and_type():
    """输入完整卷字典 → 重建 NtfsVolume，快照 serial 与输入一致。"""
    data = {
        "serial": "VOL-9",
        "device_id": "DEV-9",
        "name": "v",
        "add_time": "2026-03-01T00:00:00",
        "last_check_time": None,
        "state": VolumeState.UNKNOWN,
        "capacity": 1,
        "unique_mount_point": "ump",
        "file_system": "ntfs",
        "info": "",
        "volume_path": "/mnt/v",
    }
    vol = Volume.from_dict(data)
    assert isinstance(vol, NtfsVolume)
    snapshot = vol.to_snapshot()
    assert snapshot["serial"] == "VOL-9"
    assert snapshot["file_system"] == "ntfs"
    assert snapshot["add_time"] == "2026-03-01T00:00:00"


def test_from_dict_defaults_for_missing_optional_fields():
    """输入只有 serial 的字典 → 可选字段取默认值且回退基类。"""
    vol = Volume.from_dict({"serial": "VOL-3"})
    assert type(vol) is Volume
    assert vol.device_id == ""
    assert vol.name == ""
    assert vol.file_system is None
    assert vol.volume_path is None


def test_from_dict_volume_path_override():
    """输入字典并显式传 volume_path → 覆盖字典里的路径。"""
    vol = Volume.from_dict({"serial": "VOL-1", "volume_path": "/old"}, volume_path="/new")
    assert vol.volume_path == "/new"


def test_from_dict_keeps_dict_volume_path_when_not_overridden():
    """输入字典且不传 volume_path → 保留字典中的 volume_path。"""
    vol = Volume.from_dict({"serial": "VOL-1", "volume_path": "/keep"})
    assert vol.volume_path == "/keep"


def test_to_snapshot_fields_and_json():
    """输入完整卷 → 快照含全部 11 个字段，JSON 可反序列化且中文不转义。"""
    vol = _volume("ntfs")
    snapshot = vol.to_snapshot()
    assert set(snapshot) == SNAPSHOT_KEYS
    assert snapshot["add_time"] == "2026-02-01T12:00:00"
    assert snapshot["last_check_time"] is None

    text = vol.to_json()
    assert "数据卷" in text
    assert json.loads(text)["file_system"] == "ntfs"
    assert json.loads(text)["state"] == "healthy"


def test_to_snapshot_keeps_none_timestamps_for_base_instance():
    """输入只有 serial 的卷 → 快照时间字段为 None 且不抛错。"""
    snapshot = Volume.create(serial="VOL-1").to_snapshot()
    assert snapshot["add_time"] is None
    assert snapshot["last_check_time"] is None


def test_datas_and_meta_paths_derive_from_volume_path():
    """输入挂载路径 "/mnt/vol" → datas_path / meta_path 分别为其下 datas、meta 子目录。"""
    vol = _volume("ntfs", volume_path="/mnt/vol")
    assert vol.datas_path == "/mnt/vol/datas"
    assert vol.meta_path == "/mnt/vol/meta"


def test_datas_and_meta_paths_are_none_without_volume_path():
    """输入 volume_path=None → datas_path / meta_path 均为 None。"""
    detached = _volume("ntfs", volume_path=None)
    assert detached.datas_path is None
    assert detached.meta_path is None


def test_datas_and_meta_paths_handle_trailing_separator():
    """输入带尾斜杠的挂载路径 → 派生路径不产生重复分隔符。"""
    vol = _volume("ntfs", volume_path="/mnt/vol/")
    assert vol.datas_path == "/mnt/vol/datas"
    assert vol.meta_path == "/mnt/vol/meta"


@pytest.mark.parametrize("info", [None, "", "not-json", "[1, 2]", "{bad"])
def test_parse_info_returns_empty_for_invalid(info):
    """输入空 / 非法 JSON / 非对象 JSON → _parse_info 返回 {}。"""
    assert _volume("ntfs", info=info)._parse_info() == {}


def test_parse_info_returns_dict_for_valid_object():
    """输入合法对象 JSON → _parse_info 返回对应 dict。"""
    assert _volume("ntfs", info='{"k": 1}')._parse_info() == {"k": 1}
