from abc import ABC

from domain.storage.device.base import Device


class device_repository_abc(ABC):
    def __init__(self) -> None:
        pass

    def is_exist(self, device: Device) -> bool:
        pass

    def reg_device(self, device: Device) -> None:
        pass

    def get_device(self, serial: str) -> Device:
        pass

    def add_device(self, device: Device) -> None:
        pass

    def update_device(self, device: Device) -> None:
        pass

    def delete_device(self, serial: str) -> None:
        pass