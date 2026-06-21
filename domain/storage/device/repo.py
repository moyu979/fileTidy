from abc import ABC

from domain.storage.device.base import Device


class device_repository_abc(ABC):
    def __init__(self) -> None:
        pass

    def is_exist(self, device: Device) -> bool:
        pass

    def reg_device(self, device: Device) -> None:
        pass

    def load_device(self, serial: str) -> Device:
        pass

    def list_devices(self) -> list[Device]:
        pass

    def update_device(self, serial: str, **fields) -> None:
        """更新设备指定字段，fields 为字段名到新值的映射。"""
        pass

    def update_serial(self, old_serial: str, new_serial: str) -> None:
        """重置设备序列号，同步更新关联表中的外键引用。"""
        pass