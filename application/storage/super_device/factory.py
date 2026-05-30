import datetime

from domain.storage.device.base import Device
from domain.storage.super_device.factory import create_super_device
from domain.storage.super_device.enum import SuperDeviceState
from infra.persistence.storage.device_repository import device_repository as _DeviceRepo


class super_device_factory:

    device_repository: _DeviceRepo | None = None

    @classmethod
    def set_device_repository(cls, dr: _DeviceRepo) -> None:
        cls.device_repository = dr

    @classmethod
    def new_super_device(
        cls,
        serial: str,
        name: str,
        sdtype: str,
        need_all_devices_online: bool,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperDeviceState,
        capacity: int,
        info: str,
        devices: list,
    ):
        if serial is None:
            raise ValueError("serial is None")
        device_items = []
        for device in devices:
            if isinstance(device, Device):
                device_items.append(device.serial)
            else:
                device_items.append(device)
        for device_serial in device_items:
            if cls.device_repository is None or cls.device_repository.load_device(device_serial) is None:
                raise ValueError(f"子设备序列号 {device_serial} 不存在，无法创建超级设备")
        return create_super_device(
            serial=serial,
            name=name,
            sdtype=sdtype,
            need_all_devices_online=need_all_devices_online,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            capacity=capacity,
            info=info,
            devices=device_items,
        )