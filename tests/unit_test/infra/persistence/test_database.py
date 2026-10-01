# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/database.py —— 引擎/会话工厂构建、SQLite 外键 PRAGMA、会话上下文。

目的（测什么）：
- `build_session_factory`：返回 (sessionmaker, Engine)、sqlite URL 的专项参数、
  `autoflush/autocommit` 配置、`check_same_thread=False` 让会话可跨线程使用；
- 模块级 `Engine "connect"` 监听器：连接建立后 `PRAGMA foreign_keys=1`，
  且外键违规真的被 SQLite 拒绝（IntegrityError）；
- `session_scope`：正常退出提交、异常回滚并透传、退出后释放会话。

输入：`tmp_path` 下的临时 SQLite 库、内存库、子线程、故意违规或抛错的用例。

期望输出：会话工厂与上下文管理器行为符合各 docstring；异常类型为 `IntegrityError` / `RuntimeError` / `ValueError`。
"""

from __future__ import annotations

import threading

import pytest
from sqlalchemy.exc import IntegrityError

from infra.persistence.database import build_session_factory, session_scope
from infra.persistence.models import Base, DeviceModel, FileLocationsModel


@pytest.fixture
def db_env(tmp_path):
    """建好表（无默认数据）的 (session_factory, engine)，用例结束释放引擎。"""
    factory, engine = build_session_factory(f"sqlite:///{tmp_path / 'database.db'}")
    Base.metadata.create_all(bind=engine)
    yield factory, engine
    engine.dispose()


# ── build_session_factory ─────────────────────────────────────────


def test_build_session_factory_returns_factory_and_engine(tmp_path):
    """输入 sqlite 文件 URL → 期望输出 (sessionmaker, Engine) 且 bind/autoflush/autocommit 正确。"""
    factory, engine = build_session_factory(f"sqlite:///{tmp_path / 'a.db'}")
    try:
        assert engine.dialect.name == "sqlite"
        assert factory.kw["bind"] is engine
        assert factory.kw["autoflush"] is False
        assert factory.kw["autocommit"] is False
    finally:
        engine.dispose()


def test_build_session_factory_memory_url_is_usable():
    """输入 sqlite:///:memory: → 期望输出 可建表、写入并读回（不抛异常）。"""
    factory, engine = build_session_factory("sqlite:///:memory:")
    try:
        Base.metadata.create_all(bind=engine)
        with session_scope(factory) as session:
            session.add(DeviceModel(serial="MEM"))
        with factory() as session:
            assert session.query(DeviceModel).count() == 1
    finally:
        engine.dispose()


def test_sqlite_sessions_usable_from_other_thread(db_env):
    """输入 主线程写入后由子线程读取 → 期望输出 子线程读到 1 行（check_same_thread=False 生效）。"""
    factory, _engine = db_env
    with session_scope(factory) as session:
        session.add(DeviceModel(serial="T1"))

    result: dict = {}

    def worker() -> None:
        with session_scope(factory) as session:
            result["count"] = session.query(DeviceModel).count()

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=10)

    assert not thread.is_alive()
    assert result == {"count": 1}


# ── SQLite 外键 PRAGMA ────────────────────────────────────────────


def test_foreign_keys_pragma_enabled_on_connect(db_env):
    """输入 新建连接 → 期望输出 PRAGMA foreign_keys 为 1（连接级外键约束已开启）。"""
    _factory, engine = db_env

    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_foreign_key_violation_is_rejected(db_env):
    """输入 file_locations.now_volume 指向不存在的卷 → 期望输出 IntegrityError 且无残留行。"""
    factory, _engine = db_env

    with pytest.raises(IntegrityError):
        with session_scope(factory) as session:
            session.add(
                FileLocationsModel(
                    sha512="s", md5="m", size=1, now_path="a.txt", now_volume="GHOST"
                )
            )

    with factory() as session:
        assert session.query(FileLocationsModel).count() == 0


# ── session_scope ─────────────────────────────────────────────────


def test_session_scope_commits_on_success(db_env):
    """输入 with session_scope 内 add 一行 → 期望输出 退出后新会话可见该行。"""
    factory, _engine = db_env

    with session_scope(factory) as session:
        session.add(DeviceModel(serial="OK", name="ok"))

    with factory() as session:
        row = session.get(DeviceModel, "OK")
        assert row is not None
        assert row.name == "ok"


def test_session_scope_rolls_back_and_reraises(db_env):
    """输入 with session_scope 内 add 后抛 RuntimeError → 期望输出 异常透传且行未落库。"""
    factory, _engine = db_env

    with pytest.raises(RuntimeError, match="boom"):
        with session_scope(factory) as session:
            session.add(DeviceModel(serial="BAD"))
            session.flush()
            raise RuntimeError("boom")

    with factory() as session:
        assert session.query(DeviceModel).count() == 0


def test_session_scope_closes_session_on_success(db_env):
    """输入 正常退出 session_scope → 期望输出 会话无未结束事务、身份映射已清空。"""
    factory, _engine = db_env
    holder: dict = {}

    with session_scope(factory) as session:
        session.add(DeviceModel(serial="CLOSE"))
        holder["session"] = session

    closed = holder["session"]
    assert closed.in_transaction() is False
    assert len(closed.identity_map) == 0


def test_session_scope_closes_session_on_error(db_env):
    """输入 异常退出 session_scope → 期望输出 会话同样被释放（无未结束事务、身份映射清空）。"""
    factory, _engine = db_env
    holder: dict = {}

    with pytest.raises(ValueError, match="nope"):
        with session_scope(factory) as session:
            holder["session"] = session
            session.add(DeviceModel(serial="X"))
            raise ValueError("nope")

    closed = holder["session"]
    assert closed.in_transaction() is False
    assert len(closed.identity_map) == 0
