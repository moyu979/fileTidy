from datetime import datetime

from apps.common.database.models import DeviceModel
from apps.common.database.session import session_scope
from apps.infra.device.os_adapter import get_capacity, path2serial
from apps.infra.device.os_adapter.serial2path import serial2path
from apps.infra.device.os_adapter.get_type import get_type

from .impl.hdd_device import HddDevice
from .impl.ssd_device import SsdDevice
from .impl.tape_device import TapeDevice

def get_kind(*args,**kwargs):
    if kind in kwargs:
        kind = kwargs["kind"]
    else:
        path = kwargs["path"]
        kind = get_type(path)
    return kind

class DeviceFactory:
    def __init__(self):
        self.devices = []

    def create_device(self,*args,**kwargs):
        # 检查serial和path是否匹配
        kind = get_kind(args,kwargs)
        if kind == "HDD".lower():
            return HddDevice(args,kwargs)
        elif kind == "SSD".lower():
            return SsdDevice(args,kwargs)
        elif kind.startswith("tape"):
            return TapeDevice(args,kwargs)
        else:
            return None

    def get_device(self, serial) :
        device = DeviceModel.query.filter(DeviceModel.serial == serial).first()
        if device:
            if device.kind == "HDD":
                return HddDevice(orm_model=device, path=serial2path(serial))
            elif device.kind == "SSD":
                return SsdDevice(orm_model=device, path=serial2path(serial))
            elif device.kind == "Tape":
                return TapeDevice(orm_model=device, path=serial2path(serial))
            else:
                return None