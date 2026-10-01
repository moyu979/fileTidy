# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/defaults.py —— 默认占位记录的幂等确保。

目的（测什么）：
- `ensure_defaults` 首次执行后六张表各出现 1 条 `EXTERNAL_*` 记录，且字段值符合源码约定；
- 幂等性：同一会话内重复调用、跨会话重复调用都不新增行，也不刷新已有行的 `add_time`；
- 不覆盖既有数据：已被人工修改的占位记录、用户自定义行都原样保留；
- 结构表缺失时会被补回（存在性查询分支），且默认关联指向默认超级设备/超级卷；
- 与 `init_database` 串联后保持稳定（不会重复填充）。

输入：`tmp_path` 下全新 SQLite 库（仅建表）、同一/不同会话中多次调用。

期望输出：行数与字段值恒定；返回值 None；`add_time` 与 `last_check_time` 相等且接近当前时间。
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from infra.persistence.database import build_session_factory
from infra.persistence.defaults import ensure_defaults
from infra.persistence.init_db import init_database
from infra.persistence.models import (
    Base,
    DeviceModel,
    SuperDeviceModel,
    SuperDeviceStructureModel,
    SuperVolumeModel,
    SuperVolumeStructureModel,
    VolumeModel,
)
from domain.storage.device.enum import DeviceState
from domain.storage.super_device.enum import RelationState, SuperDeviceState
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.volume.enum import VolumeState

EXPECTED_COUNTS = {
    "device": 1,
    "super_device": 1,
    "volume": 1,
    "super_volume": 1,
    "sd_structure": 1,
    "sv_structure": 1,
}


def _utcnow() -> datetime:
    """当前 naive UTC 时间（与源码 `datetime.utcnow` 同语义，但不触发弃用告警）。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _counts(session) -> dict:
    """用给定会话统计六张表行数。"""
    return {
        "device": session.query(DeviceModel).count(),
        "super_device": session.query(SuperDeviceModel).count(),
        "volume": session.query(VolumeModel).count(),
        "super_volume": session.query(SuperVolumeModel).count(),
        "sd_structure": session.query(SuperDeviceStructureModel).count(),
        "sv_structure": session.query(SuperVolumeStructureModel).count(),
    }


@pytest.fixture
def factory(tmp_path):
    """仅建表（无默认数据）的会话工厂。"""
    session_factory, engine = build_session_factory(
        f"sqlite:///{tmp_path / 'defaults.db'}"
    )
    Base.metadata.create_all(bind=engine)
    yield session_factory
    engine.dispose()


def _seed(session_factory) -> None:
    """调用 ensure_defaults 并提交。"""
    with session_factory() as session:
        ensure_defaults(session)
        session.commit()


# ── 首次填充 ──────────────────────────────────────────────────────


def test_ensure_defaults_seeds_one_row_per_table(factory):
    """输入 空库 + 一次 ensure_defaults（自行 flush）→ 期望输出 六张表各 1 条记录且返回 None。"""
    with factory() as session:
        assert ensure_defaults(session) is None
        session.flush()
        assert _counts(session) == EXPECTED_COUNTS


def test_ensure_defaults_leaves_last_rows_pending_until_flush(factory):
    """输入 会话 autoflush=False 时未 flush 就计数 → 期望输出 最后一批待写关联行尚未计入。"""
    with factory() as session:
        ensure_defaults(session)
        # 会话工厂为 autoflush=False，查询不会自动 flush，未显式 flush 前结构行仍是 pending
        assert _counts(session)["sv_structure"] == 0
        session.flush()
        assert _counts(session)["sv_structure"] == 1


def test_ensure_defaults_device_placeholder_values(factory):
    """输入 空库 + ensure_defaults → 期望输出 默认设备是 any/HEALTHY/容量 0 的占位记录。"""
    _seed(factory)

    with factory() as session:
        device = session.get(DeviceModel, "EXTERNAL_DEVICE")
        assert device.name == "EXTERNAL_DEVICE"
        assert device.type == "any"
        assert device.state is DeviceState.HEALTHY
        assert device.capacity == 0
        assert device.info == "用于默认和缺省的类"
        assert device.add_time == device.last_check_time


def test_ensure_defaults_super_device_and_volume_values(factory):
    """输入 空库 + ensure_defaults → 期望输出 默认超级设备/卷/超级卷的字段与层级关联正确。"""
    _seed(factory)

    with factory() as session:
        super_device = session.get(SuperDeviceModel, "EXTERNAL_SUPER_DEVICE")
        assert super_device.type == "single"
        assert super_device.state is SuperDeviceState.HEALTHY
        assert super_device.capacity == 0

        volume = session.get(VolumeModel, "EXTERNAL_VOLUME")
        assert volume.device_id == "EXTERNAL_SUPER_DEVICE"
        assert volume.file_system == "any"
        assert volume.state is VolumeState.HEALTHY
        assert volume.capacity == 0
        # 未显式赋值 → 使用列默认挂载点
        assert volume.unique_mount_point == "/unknown"

        super_volume = session.get(SuperVolumeModel, "EXTERNAL_SUPERVOLUME")
        assert super_volume.type == "single"
        assert super_volume.state is SuperVolumeState.HEALTHY


def test_ensure_defaults_structure_rows_are_using(factory):
    """输入 空库 + ensure_defaults → 期望输出 两类结构表各 1 条 USING 关联，且 info 记录层级关系。"""
    _seed(factory)

    with factory() as session:
        sd_row = session.query(SuperDeviceStructureModel).one()
        assert sd_row.super_device_id == "EXTERNAL_SUPER_DEVICE"
        assert sd_row.sub_device_id == "EXTERNAL_DEVICE"
        assert sd_row.state is RelationState.USING
        assert "EXTERNAL_SUPER_DEVICE -> EXTERNAL_DEVICE" in sd_row.info

        sv_row = session.query(SuperVolumeStructureModel).one()
        assert sv_row.super_volume_id == "EXTERNAL_SUPERVOLUME"
        assert sv_row.volume_id == "EXTERNAL_VOLUME"
        assert sv_row.state is RelationState.USING
        assert "EXTERNAL_SUPERVOLUME -> EXTERNAL_VOLUME" in sv_row.info


def test_ensure_defaults_uses_current_time(factory):
    """输入 空库 + ensure_defaults → 期望输出 add_time 落在调用前后之间（当前 UTC 时间）。"""
    before = _utcnow()

    _seed(factory)

    after = _utcnow()
    with factory() as session:
        device = session.get(DeviceModel, "EXTERNAL_DEVICE")
        assert before <= device.add_time <= after
        assert device.last_check_time == device.add_time


# ── 幂等性 ────────────────────────────────────────────────────────


def test_ensure_defaults_idempotent_in_same_session(factory):
    """输入 同一会话内连续两次 ensure_defaults → 期望输出 行数与 add_time 均不变。"""
    with factory() as session:
        ensure_defaults(session)
        session.flush()
        first_counts = _counts(session)
        first_add_time = session.get(DeviceModel, "EXTERNAL_DEVICE").add_time

        ensure_defaults(session)
        session.flush()

        assert _counts(session) == first_counts == EXPECTED_COUNTS
        assert session.get(DeviceModel, "EXTERNAL_DEVICE").add_time == first_add_time


def test_ensure_defaults_idempotent_across_sessions(factory):
    """输入 两个会话先后 ensure_defaults（均提交）→ 期望输出 第二次不新增行、不改时间。"""
    _seed(factory)
    with factory() as session:
        first_add_time = session.get(DeviceModel, "EXTERNAL_DEVICE").add_time

    _seed(factory)

    with factory() as session:
        assert _counts(session) == EXPECTED_COUNTS
        assert session.get(DeviceModel, "EXTERNAL_DEVICE").add_time == first_add_time


def test_ensure_defaults_does_not_overwrite_modified_rows(factory):
    """输入 占位记录被修改后再 ensure_defaults → 期望输出 修改保留（不重置为默认值）。"""
    _seed(factory)
    with factory() as session:
        device = session.get(DeviceModel, "EXTERNAL_DEVICE")
        device.name = "renamed-by-user"
        device.state = DeviceState.FAULT
        session.commit()

    _seed(factory)

    with factory() as session:
        device = session.get(DeviceModel, "EXTERNAL_DEVICE")
        assert device.name == "renamed-by-user"
        assert device.state is DeviceState.FAULT


def test_ensure_defaults_keeps_user_rows_and_adds_placeholders(factory):
    """输入 库内已有自定义设备/卷 → 期望输出 自定义行保留，且默认占位行照常补入。"""
    with factory() as session:
        session.add(DeviceModel(serial="CUSTOM", name="custom"))
        session.add(SuperDeviceModel(serial="CUSTOM-SD", name="custom-sd"))
        session.commit()

    _seed(factory)

    with factory() as session:
        assert _counts(session)["device"] == 2
        assert _counts(session)["super_device"] == 2
        assert session.get(DeviceModel, "CUSTOM").name == "custom"
        assert session.get(DeviceModel, "EXTERNAL_DEVICE") is not None


def test_ensure_defaults_recreates_missing_structure_rows(factory):
    """输入 删掉两条结构行后 ensure_defaults → 期望输出 关联行被补回（走的是存在性查询分支）。"""
    _seed(factory)
    with factory() as session:
        session.query(SuperDeviceStructureModel).delete()
        session.query(SuperVolumeStructureModel).delete()
        session.commit()

    _seed(factory)

    with factory() as session:
        assert _counts(session)["sd_structure"] == 1
        assert _counts(session)["sv_structure"] == 1


def test_ensure_defaults_recreates_missing_device_placeholder(factory):
    """输入 删掉默认设备行（关联行仍在）后 ensure_defaults → 期望输出 设备行被补回、其余不动。"""
    _seed(factory)
    with factory() as session:
        # sub_device_id 无外键，可直接删默认设备行
        session.delete(session.get(DeviceModel, "EXTERNAL_DEVICE"))
        session.commit()

    _seed(factory)

    with factory() as session:
        assert _counts(session) == EXPECTED_COUNTS
        assert session.get(DeviceModel, "EXTERNAL_DEVICE") is not None


# ── 与 init_database 串联 ─────────────────────────────────────────


def test_ensure_defaults_after_init_database_is_stable(tmp_path):
    """输入 init_database 后再 ensure_defaults → 期望输出 行数仍为 1（两处默认填充互不重复）。"""
    session_factory, engine = build_session_factory(f"sqlite:///{tmp_path / 'combo.db'}")
    try:
        init_database(engine, session_factory)
        _seed(session_factory)
        with session_factory() as session:
            assert _counts(session) == EXPECTED_COUNTS
    finally:
        engine.dispose()
