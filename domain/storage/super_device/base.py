from abc import ABC
from datetime import datetime
from domain.storage.device.base import Device
from infra.persistence.models import SuperDeviceState

class SuperDevice(ABC):
    def __init__(self,
        serial: str,
        name: str,
        type: str,
        need_all_devices_online: bool,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperDeviceState,
        capacity: int,
        info: str,
        devices: list[Device],
    ) -> None:
        self.serial = serial
        self.name = name
        self.type = type
        self.need_all_devices_online = need_all_devices_online
        self.add_time = add_time
        self.last_check_time = last_check_time
        self.state = state
        self.capacity = capacity
        self.info = info
        self.devices = devices