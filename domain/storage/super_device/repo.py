from abc import ABC
from datetime import datetime

from domain.storage.device.base import Device
from domain.storage.super_device.base import SuperDevice


class super_device_repository_abc(ABC):
    def __init__(self) -> None:
        pass

    def is_exist(self, device: Device | str) -> bool:
        pass

    def reg_super_device(self, super_device: SuperDevice) -> None:
        pass

    def get_super_device(self,super_device_serial) -> SuperDevice:
        pass

    def list_super_device(self) -> list[SuperDevice]:
        pass

    def update_super_device(self, serial: str, **fields) -> None:
        """更新超级设备指定字段。"""
        pass

    def add_device(self, super_device_serial: str, device_serial: str, add_time: datetime) -> None:
        """向超级设备新增一个子设备。"""
        pass

    def replace_device(
        self, super_device_serial: str, old_device_serial: str,
        new_device_serial: str, add_time: datetime,
    ) -> None:
        """替换超级设备的子设备：旧设备标记 UNUSED + 记录 replaced_by，新设备新增 USING。"""
        pass

    def remove_device(self, super_device_serial: str, device_serial: str) -> None:
        """从超级设备移除一个子设备（标记 UNUSED）。"""
        pass