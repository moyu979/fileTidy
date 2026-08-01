# CHECK: 待检查 - 基础设施默认数据 - 幂等确保默认占位记录存在

# infrastructure/persistence/defaults.py

from datetime import datetime
from domain.storage.volume.enum import VolumeState
from sqlalchemy.orm import Session

from .models import (
    DeviceModel,
    SuperDeviceModel,
    SuperDeviceStructureModel,
    VolumeModel,
    SuperVolumeModel,
    SuperVolumeStructureModel,
)
from domain.storage.device.enum import DeviceState
from domain.storage.super_device.enum import RelationState, SuperDeviceState
from domain.storage.super_volume.enum import SuperVolumeState

def ensure_defaults(session: Session):
    """
    确保默认的 Device、SuperDevice、Volume 和 SuperVolume 占位记录存在。

    幂等操作：可重复执行，已存在的记录不会被重复创建。

    Args:
        session: SQLAlchemy 会话
    """
    now = datetime.utcnow()

    _ensure_device(session, now)
    _ensure_super_device(session, now)
    session.flush()
    _ensure_super_device_structure(session, now)
    _ensure_volume(session, now)
    session.flush()
    _ensure_supervolume(session, now)
    session.flush()
    _ensure_super_volume_structure(session, now)


def _ensure_device(session: Session, now: datetime):
    """
    确保默认设备记录存在，若不存在则创建。

    Args:
        session: SQLAlchemy 会话
        now: 当前 UTC 时间
    """
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
    """
    确保默认超级设备记录存在，若不存在则创建。

    Args:
        session: SQLAlchemy 会话
        now: 当前 UTC 时间
    """
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


def _ensure_super_device_structure(session: Session, now: datetime):
    """
    关联默认超级设备与默认设备。

    Args:
        session: SQLAlchemy 会话
        now: 当前 UTC 时间
    """
    exists = session.query(SuperDeviceStructureModel).filter(
        SuperDeviceStructureModel.super_device_id == "EXTERNAL_SUPER_DEVICE",
        SuperDeviceStructureModel.sub_device_id == "EXTERNAL_DEVICE",
    ).first()
    if exists is None:
        session.add(
            SuperDeviceStructureModel(
                super_device_id="EXTERNAL_SUPER_DEVICE",
                sub_device_id="EXTERNAL_DEVICE",
                add_time=now,
                state=RelationState.USING,
                info="默认关联：EXTERNAL_SUPER_DEVICE -> EXTERNAL_DEVICE",
            )
        )


def _ensure_volume(session: Session, now: datetime):
    """
    确保默认卷记录存在，若不存在则创建。

    Args:
        session: SQLAlchemy 会话
        now: 当前 UTC 时间
    """
    if session.get(VolumeModel, "EXTERNAL_VOLUME") is None:
        session.add(
            VolumeModel(
                serial="EXTERNAL_VOLUME",
                device_id="EXTERNAL_SUPER_DEVICE",
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
    """
    确保默认超级卷记录存在，若不存在则创建。

    Args:
        session: SQLAlchemy 会话
        now: 当前 UTC 时间
    """
    if session.get(SuperVolumeModel, "EXTERNAL_SUPERVOLUME") is None:
        session.add(
            SuperVolumeModel(
                serial="EXTERNAL_SUPERVOLUME",
                name="EXTERNAL_SUPERVOLUME",
                type="single",
                add_time=now,
                last_check_time=now,
                state=SuperVolumeState.HEALTHY,
                info="用于默认和缺省的类",
            )
        )


def _ensure_super_volume_structure(session: Session, now: datetime):
    """
    关联默认超级卷与默认卷。

    Args:
        session: SQLAlchemy 会话
        now: 当前 UTC 时间
    """
    exists = session.query(SuperVolumeStructureModel).filter(
        SuperVolumeStructureModel.super_volume_id == "EXTERNAL_SUPERVOLUME",
        SuperVolumeStructureModel.volume_id == "EXTERNAL_VOLUME",
    ).first()
    if exists is None:
        session.add(
            SuperVolumeStructureModel(
                super_volume_id="EXTERNAL_SUPERVOLUME",
                volume_id="EXTERNAL_VOLUME",
                add_time=now,
                state=RelationState.USING,
                info="默认关联：EXTERNAL_SUPERVOLUME -> EXTERNAL_VOLUME",
            )
        )