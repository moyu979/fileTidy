"""func_test 公共数据/查询工具。"""

from __future__ import annotations

from datetime import datetime

from domain.storage.device import Device
from domain.storage.device.enum import DeviceState
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState


def make_device(serial: str, dtype: str | None = None, **kw) -> Device:
    """构造 Device（默认 healthy）。"""
    data = {
        "serial": serial,
        "name": serial,
        "dtype": dtype,
        "add_time": datetime(2026, 1, 1),
        "last_check_time": datetime(2026, 1, 1),
        "state": kw.pop("state", DeviceState.HEALTHY),
    }
    data.update(kw)
    return Device.create(**data)


def make_super_device(serial: str, sdtype: str = "raidz", devices=None, **kw) -> SuperDevice:
    """构造 SuperDevice（默认 raidz + healthy）。"""
    return SuperDevice.create(
        serial=serial,
        name=serial,
        sdtype=sdtype,
        need_all_devices_online=kw.pop("need_all_devices_online", True),
        add_time=datetime(2026, 1, 1),
        last_check_time=datetime(2026, 1, 1),
        state=kw.pop("state", SuperDeviceState.HEALTHY),
        capacity=kw.pop("capacity", 1_000),
        info=kw.pop("info", ""),
        devices=devices or [],
    )


def make_volume(serial: str, device_id: str = "D", **kw) -> Volume:
    """构造 Volume（默认 ntfs + healthy）。"""
    return Volume.create(
        serial=serial,
        device_id=device_id,
        name=kw.pop("name", serial),
        add_time=datetime(2026, 1, 1),
        last_check_time=datetime(2026, 1, 1),
        state=kw.pop("state", VolumeState.HEALTHY),
        capacity=kw.pop("capacity", 100),
        unique_mount_point=kw.pop("unique_mount_point", "/mnt/" + serial),
        file_system=kw.pop("file_system", "ntfs"),
        info=kw.pop("info", ""),
        volume_path=kw.pop("volume_path", None),
    )


def make_super_volume(serial: str, svtype: str = "copy", volumes=None, **kw) -> SuperVolume:
    """构造 SuperVolume（默认 copy + healthy）。"""
    return SuperVolume.create(
        serial=serial,
        name=kw.pop("name", serial),
        svtype=svtype,
        method=kw.pop("method", ""),
        add_time=datetime(2026, 1, 1),
        last_check_time=datetime(2026, 1, 1),
        state=kw.pop("state", SuperVolumeState.HEALTHY),
        info=kw.pop("info", ""),
        volumes=volumes or [],
    )


def query_all(session_factory, model):
    """查询某模型全部行。"""
    with session_factory() as session:
        return list(session.query(model).all())
