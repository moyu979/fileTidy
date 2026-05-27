import datetime

from domain.storage.device.base import Device
from domain.storage.super_device.repo import super_device_repository_abc
from domain.storage.super_device.factory import create_super_device
from domain.storage.super_device.enum import SuperDeviceState


class super_device_factory:

    super_device_repository: super_device_repository_abc
    
    @classmethod
    def set_super_device_repository(cls, super_device_repository: super_device_repository_abc) -> None:
        cls.super_device_repository = super_device_repository
        
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