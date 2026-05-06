# infrastructure/persistence/seed.py

from datetime import datetime
from sqlalchemy.orm import Session

from .models import (
    DeviceModel,
    VolumeModel,
    SuperVolumeModel,
    DeviceState,
)


def seed_defaults(session: Session):
    """
    初始化默认 Device / Volume / SuperVolume
    幂等：可重复执行
    """
    now = datetime.utcnow()

    _ensure_device(session, now)
    _ensure_volume(session, now)
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


def _ensure_volume(session: Session, now: datetime):
    if session.get(VolumeModel, "EXTERNAL_VOLUME") is None:
        session.add(
            VolumeModel(
                id="EXTERNAL_VOLUME",
                super_device_id="EXTERNAL_DEVICE",
                name="EXTERNAL_VOLUME",
                file_system="any",
                add_time=now,
                last_check_time=now,
                state=DeviceState.HEALTHY,
                capacity=0,
                info="用于默认和缺省的类",
            )
        )


def _ensure_supervolume(session: Session, now: datetime):
    if session.get(SuperVolumeModel, "EXTERNAL_SUPERVOLUME") is None:
        session.add(
            SuperVolumeModel(
                id="EXTERNAL_SUPERVOLUME",
                name="EXTERNAL_SUPERVOLUME",
                type="single",
                add_time=now,
                last_check_time=now,
                state=DeviceState.HEALTHY,
                info="用于默认和缺省的类",
            )
        )