# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/models.py —— ORM 表结构、列定义、主键/外键/唯一约束、枚举列与默认值。

目的（测什么）：
- `Base.metadata` 中登记的表名集合与各模型 `__tablename__` 一一对应；
- 各表列名、主键（含复合主键）、可空性、外键指向、唯一约束与类型（BigInteger/Text/Boolean/Enum）；
- 枚举列绑定的领域枚举类，以及「枚举以成员名入库存字符串、读回仍为枚举成员」的往返行为；
- 列默认值：未赋值时由默认值填充（含显式传 None 的情况），`add_time` 为 Python 侧 callable 默认。

输入：模型类与 `Column` 元数据；`tmp_path` 下临时 SQLite 库用于落库往返验证。

期望输出：表/列/约束与源码声明一致；默认值与文档一致；枚举往返后 `is` 原枚举成员。
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Integer, Text

from infra.persistence.database import build_session_factory, session_scope
from infra.persistence.models import (
    Base,
    CacheModel,
    DeviceModel,
    FileLocationsModel,
    FileSourcesModel,
    SuperDeviceModel,
    SuperDeviceStructureModel,
    SuperVolumeModel,
    SuperVolumeStructureModel,
    VolumeModel,
)
from domain.storage.device.enum import DeviceState
from domain.storage.file.enum import FileState
from domain.storage.super_device.enum import RelationState, SuperDeviceState
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.volume.enum import VolumeState

EXPECTED_TABLES = {
    "devices",
    "super_devices",
    "super_device_structures",
    "volumes",
    "super_volumes",
    "super_volume_structures",
    "file_sources",
    "file_locations",
    "cache",
}


@pytest.fixture
def db_env(tmp_path):
    """建好全部表（无默认数据）的 (session_factory, engine)。"""
    factory, engine = build_session_factory(f"sqlite:///{tmp_path / 'models.db'}")
    Base.metadata.create_all(bind=engine)
    yield factory, engine
    engine.dispose()


# ── 表与主键 ──────────────────────────────────────────────────────


def test_metadata_registers_expected_tables():
    """输入 Base.metadata → 期望输出 恰好包含 9 张预期表。"""
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_model_tablenames_match_expected():
    """输入 各 ORM 模型类 → 期望输出 __tablename__ 与预期表名一一对应。"""
    assert {
        DeviceModel.__tablename__,
        SuperDeviceModel.__tablename__,
        SuperDeviceStructureModel.__tablename__,
        VolumeModel.__tablename__,
        SuperVolumeModel.__tablename__,
        SuperVolumeStructureModel.__tablename__,
        FileSourcesModel.__tablename__,
        FileLocationsModel.__tablename__,
        CacheModel.__tablename__,
    } == EXPECTED_TABLES


def test_composite_primary_keys():
    """输入 结构表与缓存表 → 期望输出 复合主键列与声明顺序一致。"""
    assert [
        c.name for c in SuperDeviceStructureModel.__table__.primary_key.columns
    ] == ["super_device_id", "sub_device_id"]
    assert [
        c.name for c in SuperVolumeStructureModel.__table__.primary_key.columns
    ] == ["super_volume_id", "volume_id"]
    assert [c.name for c in FileLocationsModel.__table__.primary_key.columns] == [
        "now_volume",
        "now_path",
    ]
    assert [c.name for c in CacheModel.__table__.primary_key.columns] == [
        "md5",
        "now_path",
    ]


def test_devices_columns_and_types():
    """输入 DeviceModel.__table__ → 期望输出 列名/主键/类型/默认值/可空性与声明一致。"""
    table = DeviceModel.__table__
    assert set(table.columns.keys()) == {
        "serial",
        "name",
        "type",
        "add_time",
        "last_check_time",
        "state",
        "capacity",
        "info",
    }
    assert table.columns["serial"].primary_key is True
    assert table.columns["name"].default.arg == ""
    assert table.columns["info"].default.arg == ""
    assert table.columns["info"].type.__class__ is Text
    assert isinstance(table.columns["capacity"].type, BigInteger)
    assert isinstance(table.columns["add_time"].type, DateTime)
    assert table.columns["last_check_time"].nullable is True
    assert table.columns["capacity"].nullable is True


def test_super_devices_flags_and_defaults():
    """输入 SuperDeviceModel.__table__ → 期望输出 need_all_devices_online 为 Boolean 且默认 False。"""
    table = SuperDeviceModel.__table__
    assert isinstance(table.columns["need_all_devices_online"].type, Boolean)
    assert table.columns["need_all_devices_online"].default.arg is False
    assert table.columns["name"].default.arg == ""
    assert table.columns["state"].default.arg is SuperDeviceState.HEALTHY


def test_volumes_device_id_has_no_foreign_key():
    """输入 VolumeModel.__table__ → 期望输出 device_id 非空但**不设**外键（可指向设备或超级设备）。"""
    table = VolumeModel.__table__
    assert table.columns["device_id"].nullable is False
    assert set(table.foreign_keys) == set()
    assert table.columns["unique_mount_point"].default.arg == "/unknown"
    assert table.columns["file_system"].default.arg == ""
    assert table.columns["state"].default.arg is VolumeState.UNKNOWN


def test_super_devices_structure_foreign_key_only_on_parent():
    """输入 SuperDeviceStructureModel.__table__ → 期望输出 仅父列有外键，子列可自由引用（支持层叠）。"""
    table = SuperDeviceStructureModel.__table__
    assert {
        fk.target_fullname for fk in table.columns["super_device_id"].foreign_keys
    } == {"super_devices.serial"}
    assert set(table.columns["sub_device_id"].foreign_keys) == set()
    assert table.columns["state"].default.arg is RelationState.USING


def test_super_volumes_structure_keys_and_uniqueness():
    """输入 SuperVolumeStructureModel.__table__ → 期望输出 双外键 + volume_id 唯一约束。"""
    table = SuperVolumeStructureModel.__table__
    assert {
        fk.target_fullname for fk in table.columns["super_volume_id"].foreign_keys
    } == {"super_volumes.serial"}
    assert {
        fk.target_fullname for fk in table.columns["volume_id"].foreign_keys
    } == {"volumes.serial"}
    assert table.columns["volume_id"].unique is True
    assert table.columns["volume_id"].nullable is False


def test_super_volumes_name_is_unique_and_not_null():
    """输入 SuperVolumeModel.__table__ → 期望输出 name 唯一且非空。"""
    table = SuperVolumeModel.__table__
    assert table.columns["name"].unique is True
    assert table.columns["name"].nullable is False
    assert table.columns["state"].default.arg is SuperVolumeState.HEALTHY


def test_file_tables_columns_and_constraints():
    """输入 file_sources / file_locations / cache → 期望输出 列名、非空与外键符合声明。"""
    sources = FileSourcesModel.__table__
    assert sources.columns["id"].primary_key is True
    assert sources.columns["sha512"].nullable is False
    assert sources.columns["md5"].nullable is False
    assert isinstance(sources.columns["size"].type, Integer)
    assert set(sources.foreign_keys) == set()
    # 无唯一约束：同一文件可重复登记（源码 TODO 已说明）
    assert not any(col.unique for col in sources.columns)

    locations = FileLocationsModel.__table__
    assert locations.columns["now_path"].nullable is False
    assert locations.columns["sha512"].nullable is False
    assert {
        fk.target_fullname for fk in locations.columns["now_volume"].foreign_keys
    } == {"volumes.serial"}

    cache = CacheModel.__table__
    assert cache.columns["now_name"].nullable is True
    assert cache.columns["last_visit_time"].nullable is True
    assert cache.columns["last_modify_time"].nullable is True
    assert set(cache.foreign_keys) == set()


# ── 枚举列 ────────────────────────────────────────────────────────


def test_enum_columns_bind_domain_enums():
    """输入 各枚举列 → 期望输出 绑定对应领域枚举类，且约束未启用（create_constraint=False）。"""
    expected = {
        (DeviceModel, "state"): DeviceState,
        (SuperDeviceModel, "state"): SuperDeviceState,
        (SuperDeviceStructureModel, "state"): RelationState,
        (VolumeModel, "state"): VolumeState,
        (SuperVolumeModel, "state"): SuperVolumeState,
        (SuperVolumeStructureModel, "state"): RelationState,
        (FileSourcesModel, "state"): FileState,
        (FileLocationsModel, "state"): FileState,
    }
    for (model, column_name), enum_type in expected.items():
        column_type = model.__table__.columns[column_name].type
        assert isinstance(column_type, Enum)
        assert column_type.enum_class is enum_type
        assert column_type.create_constraint is False


def test_enum_round_trip_stores_member_name(db_env):
    """输入 写入 DeviceState.DANGER → 期望输出 库内文本为 'DANGER'，读回 `is` 同一枚举成员。"""
    factory, engine = db_env

    with session_scope(factory) as session:
        session.add(DeviceModel(serial="D", state=DeviceState.DANGER))

    with engine.connect() as connection:
        stored = connection.exec_driver_sql(
            "select state from devices where serial = 'D'"
        ).scalar()
    assert stored == "DANGER"

    with factory() as session:
        assert session.get(DeviceModel, "D").state is DeviceState.DANGER


def test_enum_defaults_applied_when_unset_or_none(db_env):
    """输入 不传 state / 显式 state=None → 期望输出 都落默认枚举（UNKNOWN / ONLINE）。"""
    factory, _engine = db_env

    with session_scope(factory) as session:
        session.add(DeviceModel(serial="A"))
        session.add(DeviceModel(serial="B", state=None))
        session.add(
            FileSourcesModel(sha512="s", md5="m", size=1, state=None)
        )

    with factory() as session:
        assert session.get(DeviceModel, "A").state is DeviceState.UNKNOWN
        assert session.get(DeviceModel, "B").state is DeviceState.UNKNOWN
        assert session.query(FileSourcesModel).one().state is FileState.ONLINE


# ── 列默认值 ──────────────────────────────────────────────────────


def test_python_side_defaults_not_applied_before_flush():
    """输入 仅构造未落库的 DeviceModel → 期望输出 默认值尚未生效（None）。"""
    pending = DeviceModel(serial="P")
    assert pending.name is None
    assert pending.state is None
    assert pending.info is None


def test_defaults_filled_on_insert(db_env):
    """输入 只给 serial 的设备行 → 期望输出 name/info 为空串、state 默认 UNKNOWN、add_time 有值。"""
    factory, _engine = db_env

    with session_scope(factory) as session:
        session.add(DeviceModel(serial="D1"))

    with factory() as session:
        row = session.query(DeviceModel).one()
        assert row.name == ""
        assert row.info == ""
        assert row.state is DeviceState.UNKNOWN
        assert isinstance(row.add_time, datetime)
        assert row.capacity is None
        assert row.last_check_time is None


def test_add_time_default_is_callable():
    """输入 各表 add_time 列 → 期望输出 默认值为 callable（插入时取当前时间，而非固定值）。"""
    for model in (
        DeviceModel,
        SuperDeviceModel,
        SuperDeviceStructureModel,
        VolumeModel,
        SuperVolumeModel,
        SuperVolumeStructureModel,
        FileSourcesModel,
        FileLocationsModel,
        CacheModel,
    ):
        default = model.__table__.columns["add_time"].default
        assert default is not None, model.__name__
        assert callable(default.arg), model.__name__
        # SQLAlchemy 会用 ctx 包装 Python callable，调用结果即当前时间
        assert isinstance(default.arg(None), datetime), model.__name__
