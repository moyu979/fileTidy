from abc import ABC

from domain.storage.device.base import Device
from domain.storage.super_device.base import SuperDevice


class super_device_repository_abc(ABC):
    def __init__(self) -> None:
        pass

    def is_exist(self, device: Device) -> bool:
        pass

    def reg_super_device(self, super_device: SuperDevice) -> None:
        pass

    def get_super_device(self,super_device_serial) -> SuperDevice:
        pass

    def list_super_device(self) -> list[SuperDevice]:
        pass