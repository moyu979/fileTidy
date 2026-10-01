# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/super_volume/variants/copy —— CopySuperVolume 复制变体。

目的（测什么）：
- 验证 CopySuperVolume 的注册与工厂分派（_type_key = "copy"）；
- 验证构造函数为纯透传：入参逐字段写入实例属性（含 method）；
- 验证子卷数量不限（0 个 / 1 个 / 多个均可构造）；
- 验证快照的 type 字段为 "copy"。

输入：
- svtype = "copy" 与 volumes 列表（0 个 / 1 个 / 3 个）。

期望输出：
- 构造出 CopySuperVolume 且属性与入参一致；快照 type 为 "copy"。
"""

from __future__ import annotations

from datetime import datetime

import pytest

from domain.storage.super_volume import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.super_volume.variants.copy import CopySuperVolume


def _copy(volumes: list[str], **overrides) -> CopySuperVolume:
    """构造一个 CopySuperVolume 实例。"""
    data = {
        "serial": "CP-1",
        "name": "复制组",
        "svtype": "copy",
        "method": "rsync",
        "add_time": datetime(2026, 1, 1, 8, 0, 0),
        "last_check_time": None,
        "state": SuperVolumeState.HEALTHY,
        "info": "{}",
        "volumes": volumes,
    }
    data.update(overrides)
    return SuperVolume.create(**data)  # type: ignore[return-value]


def test_copy_is_registered_and_dispatched():
    """输入 svtype="copy" → 工厂返回 CopySuperVolume 且注册表登记该变体。"""
    assert CopySuperVolume._type_key == "copy"
    assert SuperVolume._registry["copy"] is CopySuperVolume
    assert isinstance(_copy(["V1"]), CopySuperVolume)


def test_copy_constructor_passes_through_all_fields():
    """输入全部字段 → 实例属性与入参逐一一致。"""
    sv = _copy(["V1", "V2"], name="组A", method="mirror", state=SuperVolumeState.DANGER)
    assert sv.serial == "CP-1"
    assert sv.name == "组A"
    assert sv.svtype == "copy"
    assert sv.method == "mirror"
    assert sv.add_time == datetime(2026, 1, 1, 8, 0, 0)
    assert sv.last_check_time is None
    assert sv.state is SuperVolumeState.DANGER
    assert sv.volumes == ["V1", "V2"]


@pytest.mark.parametrize("volumes", [[], ["V1"], ["V1", "V2", "V3"]])
def test_copy_accepts_any_volume_count(volumes):
    """输入 0 / 1 / 3 个子卷 → 均可构造 CopySuperVolume（不做数量断言）。"""
    assert _copy(volumes).volumes == volumes


def test_copy_is_a_super_volume():
    """输入 copy → 实例同时是 SuperVolume（继承关系成立）。"""
    assert isinstance(_copy(["V1"]), SuperVolume)


def test_copy_snapshot_type_and_method():
    """输入 copy 实例 → 快照 type 为 "copy" 且 method 原样保留。"""
    snapshot = _copy(["V1", "V2"]).to_snapshot()
    assert snapshot["type"] == "copy"
    assert snapshot["method"] == "rsync"
    assert snapshot["volumes"] == ["V1", "V2"]
