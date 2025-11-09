"""
设备工厂，用于创建和管理设备实例,同时提供对外接口
"""

from sysconfig import get_path
from component.device.drivers.HDD import HDD
from component.device.drivers.SSD import SSD
from component.device.drivers.Tape import Tape
from component.device.tools.getCapacity import get_capacity
from component.device.tools.isHdd import is_hdd
from component.device.tools.isSSD import is_ssd
from component.device.tools.isTape import is_tape
from component.device.tools.getSerial import get_serial
from database.models import DeviceModel


class DeviceFactory:
    """设备工厂，提供静态方法创建设备实例"""
    
    @staticmethod
    def createDevice(device_path):
        """
        根据设备路径创建对应的设备实例，用于新建设备时使用
        
        Args:
            device_path: 设备路径
            orm_model: 可选的ORM模型实例
            
        Returns:
            设备实例（HDD、SSD 或 Tape），如果无法识别设备类型则返回 None)
        """
        if not device_path:
            return None
    
        
        Device=DeviceModel(
            serial = get_serial(device_path),  # device_ 开头的唯一 ID
            name = "",
            kind = "",
            add_time = "",
            last_check_time = "",
            capacity = get_capacity(device_path),
            info = ""
        )
        path=get_path(device_path)

        if is_hdd(path):
            Device.kind = "HDD"
            return HDD(orm_model=Device, path=path)
        elif is_ssd(path):
            Device.kind = "SSD"
            return SSD(orm_model=Device, path=path)
        elif is_tape(path):
            Device.kind = "Tape"
            return Tape(orm_model=Device, path=path)
        else:
            Device.kind = "Unknown"
            return None

    @staticmethod
    def getDevice(device_path):
        """
        根据设备路径获取对应的设备实例，用于获取已经记录的设备
        """
        serial=get_serial(device_path)
        if serial:
            device=DeviceModel.query.filter(DeviceModel.serial == serial).first()
            if device:
                kind=device.kind
                if kind == "HDD":
                    return HDD(orm_model=device, path=device_path)
                elif kind == "SSD":
                    return SSD(orm_model=device, path=device_path)
                elif kind == "Tape":
                    return Tape(orm_model=device, path=device_path)
                else:
                    return None
            else:
                return None
        else:
            return None
        
        
