import datetime

from application.storage.device import device_factory
from domain.storage.device.base import Device
from domain.storage.super_device.variants.single_super_device import SingleSuperDevice
from infra.persistence.models import SuperDeviceState


class super_device_factory:
    @staticmethod
    def new_super_device(
        serial: str,
        name: str,
        type: str,
        need_all_devices_online: bool,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperDeviceState,
        capacity: int,
        info: str,
        devices: list[any],
    ):
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
        