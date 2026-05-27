import datetime

from domain.storage.device.base import Device

capacity_datas={
    "lto1":1024*1024*1024*1000*0.5, # 0.5TB
    "lto5":1024*1024*1024*1000*1.5, # 1.5TB
    "lto6":1024*1024*1024*1000*2.5  # 2.5TB
}
class TapeDevice(Device):
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