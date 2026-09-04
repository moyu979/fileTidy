# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/super_volume —— SuperVolume 实体、变体与结构对象。

目的：
- 验证按 svtype 的工厂分派与 from_dict 重建；
- 验证 SuperVolumeStructure 快照默认值；
- 验证 to_json 序列化。

输入：svtype / volumes 列表等字段。
期望输出：对应变体实例与完整快照。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from domain.storage.super_volume import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.super_volume.structure import SuperVolumeStructure
from domain.storage.super_volume.variants.copy import CopySuperVolume
from domain.storage.super_volume.variants.snapraid_raid5 import SnapraidRaid5SuperVolume


def _sv(svtype: str | None = "copy") -> SuperVolume:
    return SuperVolume.create(
        serial="SV-1",
        name="超级卷",
        svtype=svtype,
        method="copy",
        add_time=datetime(2026, 1, 1),
        last_check_time=None,
        state=SuperVolumeState.HEALTHY,
        info="{}",
        volumes=["V1", "V2"],
    )


@pytest.mark.parametrize(
    ("svtype", "expected"),
    [
        ("copy", CopySuperVolume),
        ("snapraid_raid5", SnapraidRaid5SuperVolume),
        (None, SuperVolume),
        ("zzz", SuperVolume),
    ],
)
def test_create_dispatches_by_svtype(svtype, expected):
    """输入 svtype → 返回对应变体类。"""
    assert isinstance(_sv(svtype), expected)


def test_create_requires_serial():
    """空 serial → ValueError。"""
    with pytest.raises(ValueError, match="serial"):
        SuperVolume.create(serial="")


def test_from_dict_roundtrip():
    """输入字典 → 重建 CopySuperVolume 且 volumes 快照是拷贝。"""
    data = {
        "serial": "SV-2",
        "name": "sv",
        "type": "copy",
        "method": "copy",
        "add_time": "2026-01-01T00:00:00",
        "last_check_time": None,
        "state": SuperVolumeState.HEALTHY,
        "info": "{}",
        "volumes": ["V1"],
    }
    sv = SuperVolume.from_dict(data)
    assert isinstance(sv, CopySuperVolume)
    snapshot = sv.to_snapshot()
    assert snapshot["volumes"] == ["V1"]
    snapshot["volumes"].append("x")
    assert sv.volumes == ["V1"]


def test_to_json():
    """to_json 可解析且含中文。"""
    text = _sv().to_json()
    assert "超级卷" in text
    assert json.loads(text)["type"] == "copy"


def test_structure_default_snapshot():
    """不传 add_time/state → 使用当前时间与 RelationState.USING。"""
    st = SuperVolumeStructure(super_volume_serial="SV-1", volume_id="V1")
    snapshot = st.to_snapshot()
    assert snapshot["super_volume_serial"] == "SV-1"
    assert snapshot["volume_id"] == "V1"
    assert snapshot["state"] == "using"
    assert snapshot["info"] == ""
