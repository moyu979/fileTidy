# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/init_db.py —— 建表与默认数据填充的编排。

目的（测什么）：
- `init_database(engine)` 只建表、不产数据；
- `init_database(engine, session_factory)` 建表并填充 `EXTERNAL_*` 默认占位记录；
- 重复调用幂等（默认数据不重复插入，`add_time` 亦不变）；
- 默认填充失败时抛出的异常会透传，且该次填充被整体回滚（不留半截数据）；
- 会话由 `init_database` 负责关闭（无需调用方手动 close）。

输入：`tmp_path` 下全新 SQLite 库、打桩的 `ensure_defaults`、计数的会话工厂。

期望输出：表存在性、行数与异常类型符合上述约定；返回值为 None。
"""

from __future__ import annotations

import pytest

import infra.persistence.init_db as init_db_mod
from infra.persistence.database import build_session_factory
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

def _counts(session_factory) -> dict:
    """统计六张受默认数据影响的表的行数。"""
    with session_factory() as session:
        return {
            "device": session.query(DeviceModel).count(),
            "super_device": session.query(SuperDeviceModel).count(),
            "volume": session.query(VolumeModel).count(),
            "super_volume": session.query(SuperVolumeModel).count(),
            "sd_structure": session.query(SuperDeviceStructureModel).count(),
            "sv_structure": session.query(SuperVolumeStructureModel).count(),
        }


@pytest.fixture
def db_env(tmp_path):
    """全新（未建表）的 (session_factory, engine)。"""
    factory, engine = build_session_factory(f"sqlite:///{tmp_path / 'init.db'}")
    yield factory, engine
    engine.dispose()


def _table_names(engine) -> set:
    """从 SQLite 读取已存在的表名（不含 sqlite 内部表）。"""
    from sqlalchemy import inspect

    return set(inspect(engine).get_table_names())


# ── 建表 ──────────────────────────────────────────────────────────


def test_init_database_without_factory_only_creates_tables(db_env):
    """输入 init_database(engine) 不传 session_factory → 期望输出 表已建、默认数据为空。"""
    _factory, engine = db_env

    assert init_database(engine) is None

    assert set(Base.metadata.tables) <= _table_names(engine)
    with engine.connect() as connection:
        assert connection.exec_driver_sql("select count(*) from devices").scalar() == 0


def test_init_database_creates_tables_even_when_called_twice(db_env):
    """输入 连续两次只建表 → 期望输出 不报错（create_all 幂等）。"""
    _factory, engine = db_env

    init_database(engine)
    assert init_database(engine) is None
    assert set(Base.metadata.tables) <= _table_names(engine)


# ── 填充默认数据 ──────────────────────────────────────────────────


def test_init_database_with_factory_seeds_defaults(db_env):
    """输入 init_database(engine, factory) → 期望输出 六张表各 1 条默认占位记录。"""
    factory, engine = db_env

    init_database(engine, factory)

    assert _counts(factory) == {
        "device": 1,
        "super_device": 1,
        "volume": 1,
        "super_volume": 1,
        "sd_structure": 1,
        "sv_structure": 1,
    }
    with factory() as session:
        assert session.get(DeviceModel, "EXTERNAL_DEVICE") is not None
        assert session.get(SuperDeviceModel, "EXTERNAL_SUPER_DEVICE") is not None
        assert session.get(VolumeModel, "EXTERNAL_VOLUME") is not None
        assert session.get(SuperVolumeModel, "EXTERNAL_SUPERVOLUME") is not None


def test_init_database_is_idempotent(db_env):
    """输入 连续两次 init_database → 期望输出 行数不变且默认设备 add_time 不变。"""
    factory, engine = db_env
    init_database(engine, factory)

    with factory() as session:
        first_add_time = session.get(DeviceModel, "EXTERNAL_DEVICE").add_time
    first_counts = _counts(factory)

    init_database(engine, factory)

    assert _counts(factory) == first_counts
    with factory() as session:
        assert session.get(DeviceModel, "EXTERNAL_DEVICE").add_time == first_add_time


def test_init_database_keeps_existing_custom_rows(db_env):
    """输入 库内已有自定义行后初始化 → 期望输出 自定义行保留，默认行追加（不互相覆盖）。"""
    factory, engine = db_env
    Base.metadata.create_all(bind=engine)
    with factory() as session:
        session.add(DeviceModel(serial="CUSTOM", name="custom"))
        session.commit()

    init_database(engine, factory)

    assert _counts(factory)["device"] == 2
    with factory() as session:
        assert session.get(DeviceModel, "CUSTOM").name == "custom"


# ── 失败与回滚 ────────────────────────────────────────────────────


def test_init_database_rolls_back_and_reraises_on_failure(db_env, monkeypatch):
    """输入 打桩 ensure_defaults 先写一行再抛错 → 期望输出 异常透传且该行未落库。"""
    factory, engine = db_env

    def boom(session):
        session.add(DeviceModel(serial="HALF", name="half"))
        raise RuntimeError("seed failed")

    monkeypatch.setattr(init_db_mod, "ensure_defaults", boom)

    with pytest.raises(RuntimeError, match="seed failed"):
        init_database(engine, factory)

    assert _counts(factory)["device"] == 0


def test_init_database_closes_its_own_session(db_env):
    """输入 正常初始化 → 期望输出 会话已关闭（无泄漏连接，可立即再次写入）。"""
    factory, engine = db_env
    init_database(engine, factory)

    with factory() as session:
        session.add(DeviceModel(serial="AFTER", name="after"))
        session.commit()
        assert session.query(DeviceModel).count() == 2


def test_init_database_skips_defaults_without_session_factory(db_env, monkeypatch):
    """输入 不传 session_factory → 期望输出 完全不调用 ensure_defaults（跳过默认数据填充）。"""
    _factory, engine = db_env

    def must_not_be_called(session):
        raise AssertionError("不应填充默认数据")

    monkeypatch.setattr(init_db_mod, "ensure_defaults", must_not_be_called)

    assert init_database(engine) is None
