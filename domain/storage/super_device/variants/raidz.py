import datetime
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState


class RaidzSuperDevice(SuperDevice):
    def __init__(self,
        serial: str,
        name: str,
        sdtype: str,
        need_all_devices_online: bool,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperDeviceState,
        capacity: int,
        info: str,
        devices: list[str],
    ):
        super().__init__(serial, name, sdtype, need_all_devices_online, add_time, last_check_time, state, capacity, info, devices)