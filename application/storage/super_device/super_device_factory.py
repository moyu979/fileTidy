import datetime

from application.storage.device.device_factory import device_factory
#from application.storage.super_device.super_device_repository import super_device_repository
from domain.storage.device.base import Device
from domain.storage.super_device.super_device_repo import super_device_repository_abc
from domain.storage.super_device.variants.single_super_device import SingleSuperDevice
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
        type: str,
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
                device_items.append(device)
            else:
                true_device=device_factory.load_device(device)
                if true_device is None:
                    raise ValueError(f"device {device} not found")
                device_items.append(true_device)
        if type=="single":
            return SingleSuperDevice(
                serial=serial,
                name=name,
                type=type,
                need_all_devices_online=need_all_devices_online,
                add_time=add_time,
                last_check_time=last_check_time,
                state=state,
                capacity=capacity,
                info=info,
                devices=device_items,
            )
        else:
            raise ValueError(f"invalid type: {type}")
        