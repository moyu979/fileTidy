# infrastructure/persistence/seed.py

from datetime import datetime
from domain.storage.volume.enum import VolumeState
from sqlalchemy.orm import Session

from .models import (
    DeviceModel,
    DeviceStructureModel,
    SuperDeviceModel,
    VolumeModel,
    SuperVolumeModel,
)
from domain.storage.device.enum import DeviceState
from domain.storage.super_device.enum import RelationState, SuperDeviceState

def seed_defaults(session: Session):
    """
    初始化默认 Device / Volume / SuperVolume
    幂等：可重复执行
    """
    now = datetime.utcnow()

    _ensure_device(session, now)
    _ensure_super_device(session, now)
    session.flush()
    _ensure_device_structure(session, now)
    _ensure_volume(session, now)
    session.flush()
    _ensure_supervolume(session, now)


def _ensure_device(session: Session, now: datetime):
    if session.get(DeviceModel, "EXTERNAL_DEVICE") is None:
        session.add(
            DeviceModel(
                serial="EXTERNAL_DEVICE",
                name="EXTERNAL_DEVICE",
                type="any",
                add_time=now,
                last_check_time=now,
                state=DeviceState.HEALTHY,
                capacity=0,
                info="用于默认和缺省的类",
            )
        )


def _ensure_super_device(session: Session, now: datetime):
    if session.get(SuperDeviceModel, "EXTERNAL_SUPER_DEVICE") is None:
        session.add(
            SuperDeviceModel(
                serial="EXTERNAL_SUPER_DEVICE",
                name="EXTERNAL_SUPER_DEVICE",
                type="single",
                add_time=now,
                last_check_time=now,
                state=SuperDeviceState.HEALTHY,
                capacity=0,
                info="用于默认和缺省的类",
            )
        )


def _ensure_device_structure(session: Session, now: datetime):
    """关联默认 SuperDevice 与默认 Device"""
    exists = session.query(DeviceStructureModel).filter(
        DeviceStructureModel.super_device_id == "EXTERNAL_SUPER_DEVICE",
        DeviceStructureModel.sub_device_id == "EXTERNAL_DEVICE",
    ).first()
    if exists is None:
        session.add(
            DeviceStructureModel(
                super_device_id="EXTERNAL_SUPER_DEVICE",
                sub_device_id="EXTERNAL_DEVICE",
                add_time=now,
                state=RelationState.USING,
                info="默认关联：EXTERNAL_SUPER_DEVICE -> EXTERNAL_DEVICE",
            )
        )


def _ensure_volume(session: Session, now: datetime):
    if session.get(VolumeModel, "EXTERNAL_VOLUME") is None:
        session.add(
            VolumeModel(
                serial="EXTERNAL_VOLUME",
                super_device_id="EXTERNAL_SUPER_DEVICE",
                name="EXTERNAL_VOLUME",
                file_system="any",
                add_time=now,
                last_check_time=now,
                state=VolumeState.HEALTHY,
                capacity=0,
                info="用于默认和缺省的类",
            )
        )


def _ensure_supervolume(session: Session, now: datetime):
    if session.get(SuperVolumeModel, "EXTERNAL_SUPERVOLUME") is None:
        session.add(
            SuperVolumeModel(
                serial="EXTERNAL_SUPERVOLUME",
                name="EXTERNAL_SUPERVOLUME",
                type="single",
                add_time=now,
                last_check_time=now,
                state=DeviceState.HEALTHY,
                info="用于默认和缺省的类",
            )
        )