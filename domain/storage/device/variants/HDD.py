import datetime

from domain.storage.device.base import Device


class HddDevice(Device):
    def __init__(self, 
    serial: str,
    name: str,
    dtype: str|None,
    add_time,
    last_check_time,
    capacity: int|None,
    info: str|None,
    state: str|None,
    device_path: str|None,
    ) -> None:
        super().__init__(serial, 
            name, 
            dtype, 
            add_time, 
            last_check_time, 
            capacity, 
            info, 
            state,
            device_path)

    def check(self):
        pass

    def set(self, key, value):
        pass