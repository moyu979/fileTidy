import datetime

from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState


class ManualCopySuperVolume(SuperVolume):
    def __init__(self,
        serial: str,
        name: str,
        svtype: str,
        method: str,
        add_time: datetime.datetime,
        last_check_time: datetime.datetime,
        state: SuperVolumeState,
        info: str,
        volumes: list[str],
    ):
        super().__init__(serial, name, svtype, method,
                         add_time, last_check_time, state, info, volumes)
