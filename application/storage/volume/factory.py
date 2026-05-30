from domain.storage.volume.base import Volume
from domain.storage.volume.factory import create_volume
from infra.system.storage.volume.get_path import get_path


class volume_factory:

    @classmethod
    def new_volume(
        cls,
        serial: str | None,
        device_id: str,
        name: str,
        add_time,
        last_check_time,
        state: str | None,
        capacity: int | None,
        unique_mount_point: str | None,
        file_system: str | None,
        info: str | None,
        volume_path: str | None,
    ) -> Volume:
        if serial is None:
            raise ValueError("serial is None")

        if volume_path is None:
            volume_path = get_path(serial)

        return create_volume(
            serial=serial,
            device_id=device_id,
            name=name,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            capacity=capacity,
            unique_mount_point=unique_mount_point,
            file_system=file_system,
            info=info,
            volume_path=volume_path,
        )