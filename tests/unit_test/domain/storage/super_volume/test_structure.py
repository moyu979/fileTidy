# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/super_volume/structure —— SuperVolumeStructure 关联关系领域对象。

目的（测什么）：
- 验证默认构造：add_time 缺省时取当前时间、state 默认 SuperVolumeRelationState.USING、info 默认空串；
- 验证显式字段透传（含 SuperVolumeRelationState.REPLACED）；
- 验证 to_snapshot 字段集合与取值（state 输出枚举 value、add_time 输出 ISO 字符串）。

输入：
- 定位字段（super_volume_serial / volume_id）；
- 可选字段（add_time / state / info）的有无与取值。

期望输出：
- 快照含 5 个键；默认 state 为 "using"、info 为 ""；
- 显式传入时原样反映，state 为 "replaced"，add_time 为 ISO 格式。
"""

from __future__ import annotations

from datetime import datetime

from domain.storage.super_volume.enum import SuperVolumeRelationState
from domain.storage.super_volume.structure import SuperVolumeStructure

SNAPSHOT_KEYS = {"super_volume_serial", "volume_id", "add_time", "state", "info"}


def test_default_state_and_info():
    """不传 state / info → 快照 state 为 "using"、info 为空串。"""
    st = SuperVolumeStructure(super_volume_serial="SV-1", volume_id="V1")
    snapshot = st.to_snapshot()
    assert snapshot["super_volume_serial"] == "SV-1"
    assert snapshot["volume_id"] == "V1"
    assert snapshot["state"] == "using"
    assert snapshot["info"] == ""


def test_default_add_time_is_now():
    """不传 add_time → 取当前时间，快照输出其 ISO 字符串。"""
    before = datetime.now()
    st = SuperVolumeStructure(super_volume_serial="SV-1", volume_id="V1")
    after = datetime.now()
    assert before <= st.add_time <= after
    assert st.to_snapshot()["add_time"] == st.add_time.isoformat()


def test_explicit_fields_and_replaced_state():
    """传入全部字段 → 快照与入参一致，state 为 "replaced"。"""
    st = SuperVolumeStructure(
        super_volume_serial="SV-9",
        volume_id="V9",
        add_time=datetime(2026, 5, 1, 10, 0, 0),
        state=SuperVolumeRelationState.REPLACED,
        info='{"k": 1}',
    )
    assert st.to_snapshot() == {
        "super_volume_serial": "SV-9",
        "volume_id": "V9",
        "add_time": "2026-05-01T10:00:00",
        "state": "replaced",
        "info": '{"k": 1}',
    }


def test_snapshot_key_set_is_stable():
    """构造默认实例 → 快照键集合恰为 5 个约定字段。"""
    assert set(SuperVolumeStructure("SV-1", "V1").to_snapshot()) == SNAPSHOT_KEYS


def test_positional_arguments_follow_signature_order():
    """按位置传参（serial, volume_id, add_time, state, info）→ 字段各就各位。"""
    st = SuperVolumeStructure(
        "SV-1", "V1", datetime(2026, 1, 1), SuperVolumeRelationState.REPLACED, "note"
    )
    snapshot = st.to_snapshot()
    assert snapshot["super_volume_serial"] == "SV-1"
    assert snapshot["volume_id"] == "V1"
    assert snapshot["add_time"] == "2026-01-01T00:00:00"
    assert snapshot["state"] == "replaced"
    assert snapshot["info"] == "note"


def test_state_attribute_keeps_enum_instance():
    """传入 SuperVolumeRelationState → 实例属性保持枚举实例（快照才转字符串）。"""
    st = SuperVolumeStructure("SV-1", "V1", state=SuperVolumeRelationState.USING)
    assert st.state is SuperVolumeRelationState.USING
