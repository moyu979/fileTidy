from abc import ABC

from domain.storage.volume.base import Volume


class volume_repository_abc(ABC):
    def __init__(self) -> None:
        pass

    def is_exist(self, volume: Volume) -> bool:
        pass

    def reg_volume(self, volume: Volume) -> None:
        pass

    def get_volume(self, volume_id:str)->Volume:
        pass

    def list_volume(self)->list[Volume]:
        pass
