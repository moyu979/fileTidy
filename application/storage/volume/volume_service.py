
from multiprocessing import set_forkserver_preload
from application.storage.volume import volume_factory
from domain.storage.device.base import Device as DeviceBase
from domain.storage.volume.events import VolumeRegistered
from domain.storage.volume.volume_repo import volume_repository_abc as VolumeRepository
from domain.storage.device.device_repo import device_repository_abc as DeviceRepository
from infra.operate_log.operate_log import log_event
from infra.persistence.storage import device_repository

class volume_service:
    def __init__(self, volume_repository: VolumeRepository,device_repository: DeviceRepository) -> None:
        self.volume_repository = volume_repository
        self.device_repository = device_repository

    def reg_volume(self,
        id: str,
        name: str,
        type: str,
        method: str,

        add_time,
        last_check_time,
        state: str|None,

        capacity: int|None,
        unique_mount_point: str|None,
        file_system: str|None,
        info: str|None,
        
        volume_path: str|None,
        based_on: list[DeviceBase]|None,
    ):
        volume=volume_factory.new_volume(
            id=id,
            name=name,
            type=type,

            method=method,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            capacity=capacity,
            unique_mount_point=unique_mount_point,
            file_system=file_system,
            info=info,
            volume_path=volume_path,
            based_on=based_on,
        )
        # 判断1: 
        if self.volume_repository.is_exist(volume):
            raise ValueError(f"volume {id} already exists")
        self.volume_repository.reg_device(volume)
        log_event(VolumeRegistered(volume))
        return volume

        
        