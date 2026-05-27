import stat
from domain.storage.device.base import Device as DeviceBase
from domain.storage.volume.base import Volume
from domain.storage.volume.variants.ntfs import ntfs
from infra.system.storage.volume.get_id import get_id
from infra.system.storage.volume.get_path import get_path


class volume_factory:
    def __init__(self) -> None:
        pass
    @classmethod
    def new_volume(cls,
        serial: str|None,
        super_device_id: str,
        name: str,
    
        add_time,
        last_check_time,
        state: str|None,

        capacity: int|None,
        unique_mount_point: str|None,
        file_system: str|None,
        info: str|None,
        
        volume_path: str|None,
    ) -> Volume:
        if file_system == "ntfs":
            return ntfs(
                serial,
                super_device_id,
                name,
                add_time,
                last_check_time,
                state,
                capacity,
                unique_mount_point,
                file_system,
                info,
                volume_path,
            )