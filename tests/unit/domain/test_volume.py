# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/volume —— Volume 实体与文件系统变体。

目的：
- 验证按 file_system 的工厂分派、serial 必填校验与 from_dict 重建；
- 验证 datas/meta 路径属性与 info 解析兜底。

输入：file_system 字符串 / 卷字段字典 / 挂载路径。
期望输出：对应变体实例、正确的路径派生、序列化快照。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from domain.storage.volume import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.variants.exfat import ExfatVolume
from domain.storage.volume.variants.fat32 import Fat32Volume
from domain.storage.volume.variants.ltfs import LtfsVolume
from domain.storage.volume.variants.ntfs import NtfsVolume


def _volume(dtype: str | None = None, **overrides) -> Volume:
    data = {
        "serial": "VOL-1",
        "device_id": "DEV-1",
        "name": "数据卷",
        "add_time": datetime(2026, 2, 1, 12, 0, 0),
        "last_check_time": None,
        "state": VolumeState.HEALTHY,
        "capacity": 2_000_000_000_000,
        "unique_mount_point": "/mnt/vol",
        "file_system": dtype,
        "info": "{}",
        "volume_path": "/mnt/vol",
    }
    data.update(overrides)
    return Volume.create(**data)


@pytest.mark.parametrize(
    ("fs", "expected"),
    [
        ("ntfs", NtfsVolume),
        ("exfat", ExfatVolume),
        ("fat32", Fat32Volume),
        ("ltfs", LtfsVolume),
        (None, Volume),
        ("ext4", Volume),  # 未注册的文件系统回退基类
    ],
)
def test_create_dispatches_by_file_system(fs, expected):
    """输入 file_system → 期望返回对应变体类。"""
    assert isinstance(_volume(fs), expected)


def test_create_requires_serial():
    """空 serial → ValueError。"""
    with pytest.raises(ValueError, match="serial"):
        Volume.create(serial="")


def test_from_dict_roundtrip():
    """输入完整卷字典 → from_dict 快照与输入一致，类型为 NtfsVolume。"""
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
    assert vol.to_snapshot()["serial"] == "VOL-9"


def test_datas_and_meta_paths():
    """输入挂载路径 → datas_path/meta_path 派生正确；无路径 → None。"""
    vol = _volume("ntfs", volume_path="/mnt/vol")
    assert vol.datas_path == "/mnt/vol/datas"
    assert vol.meta_path == "/mnt/vol/meta"

    detached = _volume("ntfs", volume_path=None)
    assert detached.datas_path is None
    assert detached.meta_path is None


def test_to_json_roundtrip():
    """完整卷 → to_json 可反序列化且中文原样保留。"""
    text = _volume("ntfs").to_json()
    assert "数据卷" in text
    assert json.loads(text)["file_system"] == "ntfs"


@pytest.mark.parametrize("info", [None, "", "{bad", "[1]"])
def test_parse_info_fallback(info):
    """非法 info → {}。"""
    assert _volume("ntfs", info=info)._parse_info() == {}


def test_parse_info_valid():
    """合法 JSON 对象 → dict。"""
    assert _volume("ntfs", info='{"k": 1}')._parse_info() == {"k": 1}
