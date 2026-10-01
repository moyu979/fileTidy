# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/super_volume/variants/snapraid_raid5 —— SnapRAID RAID5 变体。

目的（测什么）：
- 验证 SnapraidRaid5SuperVolume 的注册与工厂分派（_type_key = "snapraid_raid5"）；
- 验证构造函数为纯透传：入参逐字段写入实例属性；
- 验证子卷数量不限（0 个 / 1 个 / 多个均可构造）；
- 验证快照的 type 字段为 "snapraid_raid5"。

输入：
- svtype = "snapraid_raid5" 与 volumes 列表（0 个 / 1 个 / 3 个）。

期望输出：
- 构造出 SnapraidRaid5SuperVolume 且属性与入参一致；快照 type 为 "snapraid_raid5"。
"""

from __future__ import annotations

from datetime import datetime

import pytest

from domain.storage.super_volume import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.super_volume.variants.snapraid_raid5 import SnapraidRaid5SuperVolume


def _snapraid(volumes: list[str], **overrides) -> SnapraidRaid5SuperVolume:
    """构造一个 SnapraidRaid5SuperVolume 实例。"""
    data = {
        "serial": "SR-1",
        "name": "snapraid组",
        "svtype": "snapraid_raid5",
        "method": "snapraid",
        "add_time": datetime(2026, 1, 1, 8, 0, 0),
        "last_check_time": None,
        "state": SuperVolumeState.HEALTHY,
        "info": '{"parity": 1}',
        "volumes": volumes,
    }
    data.update(overrides)
    return SuperVolume.create(**data)  # type: ignore[return-value]


def test_snapraid_is_registered_and_dispatched():
    """输入 svtype="snapraid_raid5" → 工厂返回 SnapraidRaid5SuperVolume 且注册表登记该变体。"""
    assert SnapraidRaid5SuperVolume._type_key == "snapraid_raid5"
    assert SuperVolume._registry["snapraid_raid5"] is SnapraidRaid5SuperVolume
    assert isinstance(_snapraid(["V1"]), SnapraidRaid5SuperVolume)


def test_snapraid_constructor_passes_through_all_fields():
    """输入全部字段 → 实例属性与入参逐一一致。"""
    sv = _snapraid(["V1", "V2", "V3"], name="组B", method="snapraid_raid5",
                   state=SuperVolumeState.DANGER)
    assert sv.serial == "SR-1"
    assert sv.name == "组B"
    assert sv.svtype == "snapraid_raid5"
    assert sv.method == "snapraid_raid5"
    assert sv.add_time == datetime(2026, 1, 1, 8, 0, 0)
    assert sv.last_check_time is None
    assert sv.state is SuperVolumeState.DANGER
    assert sv.volumes == ["V1", "V2", "V3"]


@pytest.mark.parametrize("volumes", [[], ["V1"], ["V1", "V2", "V3"]])
def test_snapraid_accepts_any_volume_count(volumes):
    """输入 0 / 1 / 3 个子卷 → 均可构造 SnapraidRaid5SuperVolume（不做数量断言）。"""
    assert _snapraid(volumes).volumes == volumes


def test_snapraid_is_a_super_volume():
    """输入 snapraid_raid5 → 实例同时是 SuperVolume（继承关系成立）。"""
    assert isinstance(_snapraid(["V1"]), SuperVolume)


def test_snapraid_snapshot_type_and_info():
    """输入 snapraid 实例 → 快照 type 为 "snapraid_raid5" 且 info 原样保留。"""
    snapshot = _snapraid(["V1", "V2"]).to_snapshot()
    assert snapshot["type"] == "snapraid_raid5"
    assert snapshot["info"] == '{"parity": 1}'
    assert snapshot["volumes"] == ["V1", "V2"]
