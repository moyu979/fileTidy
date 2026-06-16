from domain.storage.volume.base import Volume
from domain.storage.volume.repo import volume_repository_abc
from infra.persistence.database import session_scope
from infra.persistence.models import DeviceModel, SuperDeviceModel, VolumeModel


class volume_repository(volume_repository_abc):
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory
        super().__init__()

    def is_exist(self, volume: Volume) -> bool:
        with session_scope(self.session_factory) as session:
            return session.query(VolumeModel).filter(VolumeModel.serial == volume.serial).first() is not None

    def reg_volume(self, volume: Volume) -> None:
        volume_model = VolumeModel(
            serial=volume.serial,
            super_device_id=volume.device_id,
            name=volume.name,
            add_time=volume.add_time,
            last_check_time=volume.last_check_time,
            state=volume.state,
            capacity=volume.capacity,
            unique_mount_point=volume.unique_mount_point
            if volume.unique_mount_point is not None
            else "None",
            file_system=volume.file_system,
            info=volume.info if volume.info is not None else "",
        )
        with session_scope(self.session_factory) as session:
            # 兜底校验：super_device_id 必须是存在的 Device 或 SuperDevice
            device_exists = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == volume.device_id)
                .first()
                is not None
            )
            super_device_exists = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == volume.device_id)
                .first()
                is not None
            )
            if not device_exists and not super_device_exists:
                raise ValueError(
                    f"super_device_id '{volume.device_id}' 既不是有效 Device，也不是有效 SuperDevice"
                )
            session.add(volume_model)
            session.commit()

