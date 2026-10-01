"""功能测试：数据库建表与默认占位数据。

目的：init_database 后四类实体与两类结构表存在默认占位行，
重复 init_database 保持幂等。

输入：全新 sqlite 临时库 + init_database 两次。
期望输出：EXTERNAL_* 记录各一条，且记录数不随二次初始化增加。
"""

from __future__ import annotations

from infra.persistence.database import build_session_factory
from infra.persistence.init_db import init_database
from infra.persistence.models import (
    DeviceModel,
    SuperDeviceModel,
    SuperDeviceStructureModel,
    SuperVolumeModel,
    SuperVolumeStructureModel,
    VolumeModel,
)


def _counts(session_factory):
    with session_factory() as session:
        return {
            "device": session.query(DeviceModel).count(),
            "super_device": session.query(SuperDeviceModel).count(),
            "volume": session.query(VolumeModel).count(),
            "super_volume": session.query(SuperVolumeModel).count(),
            "sd_structure": session.query(SuperDeviceStructureModel).count(),
            "sv_structure": session.query(SuperVolumeStructureModel).count(),
        }


def test_init_database_seeds_defaults(seeded_session_factory):
    """首次初始化 → 默认占位记录各一条，层级关系完整。"""
    sf = seeded_session_factory
    counts = _counts(sf)
    assert counts == {
        "device": 1,
        "super_device": 1,
        "volume": 1,
        "super_volume": 1,
        "sd_structure": 1,
        "sv_structure": 1,
    }

    with sf() as session:
        assert session.get(DeviceModel, "EXTERNAL_DEVICE") is not None
        assert session.get(SuperDeviceModel, "EXTERNAL_SUPER_DEVICE") is not None
        assert session.get(VolumeModel, "EXTERNAL_VOLUME") is not None
        assert session.get(SuperVolumeModel, "EXTERNAL_SUPERVOLUME") is not None


def test_init_database_is_idempotent(tmp_path):
    """连续两次 init_database → 记录数不变。"""
    session_factory, engine = build_session_factory(
        f"sqlite:///{tmp_path / 'app.db'}"
    )
    try:
        init_database(engine, session_factory)
        first = _counts(session_factory)
        init_database(engine, session_factory)
        second = _counts(session_factory)
        assert first == second
    finally:
        engine.dispose()
