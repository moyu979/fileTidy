"""
设备工厂，用于创建和管理设备实例,同时提供对外接口
"""

from component.device.drivers.HDD import HDD
from component.device.drivers.SSD import SSD
from component.device.drivers.Tape import Tape
from component.device.tools.isHdd import is_hdd
from component.device.tools.isSSD import is_ssd
from component.device.tools.isTape import is_tape


class DeviceFactory:
    """设备工厂，提供静态方法创建设备实例"""
    
    @staticmethod
    def createDevice(device_path, orm_model=None):
        """
        根据设备路径创建对应的设备实例
        
        Args:
            device_path: 设备路径
            orm_model: 可选的ORM模型实例
            
        Returns:
            设备实例（HDD、SSD 或 Tape），如果无法识别设备类型则返回 None
        """
        if not device_path:
            return None
        
        # 判断设备类型并创建对应的设备实例
        if is_hdd(device_path):
            return HDD(orm_model=orm_model, path=device_path)
        elif is_ssd(device_path):
            return SSD(orm_model=orm_model, path=device_path)
        elif is_tape(device_path):
            return Tape(orm_model=orm_model, path=device_path)
        else:
            return None
