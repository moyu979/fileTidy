from datetime import datetime

from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState


class LtfsVolume(Volume):
    def __init__(
        self,
        serial: str,
        device_id: str,
        name: str,
        add_time: datetime,
        last_check_time: datetime,
        state: str | VolumeState,
        capacity: int | None,
        unique_mount_point: str | None,
        file_system: str,
        info: str | None,
        volume_path: str | None,
    ) -> None:
        super().__init__(
            serial, device_id, name, add_time, last_check_time,
            state, capacity, unique_mount_point, file_system, info, volume_path,
        )
