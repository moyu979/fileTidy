from abc import ABC

from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.structure import SuperVolumeStructure


class super_volume_repository_abc(ABC):
    def __init__(self) -> None:
        pass

    def is_exist(self, super_volume: SuperVolume | str) -> bool:
        pass

    def reg_super_volume(self, super_volume: SuperVolume) -> None:
        pass

    def get_super_volume(self, super_volume_serial: str) -> SuperVolume:
        pass

    def list_super_volume(self) -> list[SuperVolume]:
        pass

    def add_volumes(
        self,
        structures: list[SuperVolumeStructure],
    ) -> None:
        """向已存在的超级卷添加一批子卷关联。"""
        pass
