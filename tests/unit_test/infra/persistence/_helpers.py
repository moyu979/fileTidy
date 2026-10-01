# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""tests/unit_test/infra/persistence 专用支撑模块（非测试文件，pytest 不收集）。

目的（测什么）：为 persistence 层单测提供「独立 SQLite 库 + 五个真实仓储 + 领域对象工厂」，
       使单测不依赖 tests/func_test/conftest.py 与 tests/func_test/_helpers.py。
输入：tmp_path 下的临时库路径、各领域对象的字段覆盖参数。
期望输出：UnitDb（会话工厂 / 引擎 / 仓储字典）与可直接注册的领域对象。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.engine import Engine

from domain.storage.device.base import Device
from domain.storage.device.enum import DeviceState
from domain.storage.file.enum import FileState
from domain.storage.file.new_file import NewFile
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState
from infra.persistence.database import build_session_factory
from infra.persistence.models import Base
from infra.persistence.storage.device_repository import DeviceRepository
from infra.persistence.storage.file_repository import FileRepository
from infra.persistence.storage.super_device_repository import SuperDeviceRepository
from infra.persistence.storage.super_volume_repository import SuperVolumeRepository
from infra.persistence.storage.volume_repository import VolumeRepository

# 固定时间戳，避免用例依赖「当前时间」
FIXED_TIME = datetime(2026, 1, 1, 0, 0, 0)


@dataclass
class UnitDb:
    """一次单测独占的 SQLite 库句柄（用例结束调用 dispose() 释放引擎）。"""

    factory: Any
    engine: Engine
    repos: dict[str, Any] = field(default_factory=dict)

    def new_session(self):
        """创建一个新会话（调用方负责 close）。"""
        return self.factory()

    def dispose(self) -> None:
        """释放底层 SQLAlchemy 引擎。"""
        self.engine.dispose()


def new_db(db_path: Path, *, with_defaults: bool = False) -> UnitDb:
    """新建独立 SQLite 库并装配五个真实仓储。

    Args:
        db_path: 临时库文件路径。
        with_defaults: 为 True 时按启动流程（init_database）建表并填充默认占位记录；
            为 False 时只建表。

    Returns:
        UnitDb 句柄（含会话工厂、引擎、仓储字典）。
    """
    factory, engine = build_session_factory(f"sqlite:///{db_path}")
    if with_defaults:
        from infra.persistence.init_db import init_database

        init_database(engine, factory)
    else:
        Base.metadata.create_all(bind=engine)
    return UnitDb(
        factory=factory,
        engine=engine,
        repos={
            "device": DeviceRepository(factory),
            "volume": VolumeRepository(factory),
            "super_device": SuperDeviceRepository(factory),
            "super_volume": SuperVolumeRepository(factory),
            "file": FileRepository(factory),
        },
    )


def query_all(db: UnitDb, model) -> list:
    """用新会话查询某模型全部行（读取已提交数据）。"""
    with db.factory() as session:
        return list(session.query(model).all())


def count(db: UnitDb, model) -> int:
    """用新会话统计某模型行数。"""
    with db.factory() as session:
        return session.query(model).count()


def seed_volumes(db: UnitDb, serials=("V1",), device_serial: str = "D1") -> None:
    """登记一个设备，并在其上注册若干卷（卷的 device_id 校验需要设备先存在）。"""
    db.repos["device"].reg_device(make_device(device_serial))
    for serial in serials:
        db.repos["volume"].reg_volume(make_volume(serial, device_id=device_serial))


def make_device(serial: str, dtype: str | None = None, **kw) -> Device:
    """构造 Device（默认 healthy、固定时间），额外字段用关键字覆盖。"""
    data = {
        "serial": serial,
        "name": serial,
        "dtype": dtype,
        "add_time": FIXED_TIME,
        "last_check_time": FIXED_TIME,
        "state": kw.pop("state", DeviceState.HEALTHY),
    }
    data.update(kw)
    return Device.create(**data)


def make_super_device(
    serial: str, sdtype: str = "raidz", devices=None, **kw
) -> SuperDevice:
    """构造 SuperDevice（默认 raidz + healthy），额外字段用关键字覆盖。"""
    return SuperDevice.create(
        serial=serial,
        name=kw.pop("name", serial),
        sdtype=sdtype,
        need_all_devices_online=kw.pop("need_all_devices_online", True),
        add_time=kw.pop("add_time", FIXED_TIME),
        last_check_time=kw.pop("last_check_time", FIXED_TIME),
        state=kw.pop("state", SuperDeviceState.HEALTHY),
        capacity=kw.pop("capacity", 1000),
        info=kw.pop("info", ""),
        devices=devices or [],
    )


def make_volume(serial: str, device_id: str = "D1", **kw) -> Volume:
    """构造 Volume（默认 ntfs + healthy），额外字段用关键字覆盖。"""
    return Volume.create(
        serial=serial,
        device_id=device_id,
        name=kw.pop("name", serial),
        add_time=kw.pop("add_time", FIXED_TIME),
        last_check_time=kw.pop("last_check_time", FIXED_TIME),
        state=kw.pop("state", VolumeState.HEALTHY),
        capacity=kw.pop("capacity", 100),
        unique_mount_point=kw.pop("unique_mount_point", "/mnt/" + serial),
        file_system=kw.pop("file_system", "ntfs"),
        info=kw.pop("info", ""),
        volume_path=kw.pop("volume_path", None),
    )


def make_super_volume(serial: str, svtype: str = "copy", volumes=None, **kw) -> SuperVolume:
    """构造 SuperVolume（默认 copy + healthy），额外字段用关键字覆盖。"""
    return SuperVolume.create(
        serial=serial,
        name=kw.pop("name", serial),
        svtype=svtype,
        method=kw.pop("method", ""),
        add_time=kw.pop("add_time", FIXED_TIME),
        last_check_time=kw.pop("last_check_time", FIXED_TIME),
        state=kw.pop("state", SuperVolumeState.HEALTHY),
        info=kw.pop("info", ""),
        volumes=volumes or [],
    )


def make_new_file(
    sha512: str = "s1",
    md5: str = "m1",
    size: int = 10,
    *,
    path: str | Path = "/outside/a.txt",
    now_path: str | Path = "dir/a.txt",
    now_volume: str = "V1",
    add_time: datetime | None = FIXED_TIME,
    state: Any = FileState.ONLINE,
    info: str = "",
) -> NewFile:
    """构造 NewFile（默认 online、固定时间）。"""
    return NewFile(
        sha512=sha512,
        md5=md5,
        size=size,
        add_time=add_time,
        path=path,
        now_path=now_path,
        now_volume=now_volume,
        state=state,
        info=info,
    )
