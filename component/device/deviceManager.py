"""
设备管理器，用于管理设备实例
"""

import logging
from component.device.deviceFactory import DeviceFactory
from component.device.tools import getSerial
from component.device.tools.getCapacity import get_capacity
from component.device.tools.getNormalizedPath import get_normalized_path
from component.device.tools.Serial2Path import serial_to_path
from database.session import session_scope


class DeviceManager:
    """设备管理器，管理设备实例"""
    
    def __init__(self):
        self.devices = []
    
    def regDevice(self, device_path):
        """
        注册设备到数据库
        """
        device=DeviceFactory.createDevice(device_path)
        with session_scope() as session:
            session.add(device)
            
    def checkDevice(self, device_path):
        """
        检查设备的介质情况
        """
        device=DeviceFactory.getDevice(device_path)
        device.check()
        
    def replaceDevice(self, device_path1, device_path2):
        """
        用device_path1的设备替换掉device_path2的设备，先用get_device_role判断设备在卷中的角色，然后根据角色进行替换
        """
        logging.info(f"用{device_path1}的设备替换掉{device_path2}的设备的功能还没完成")

    def exists_in_database(self, device_path=None, serial=None):
        """
        检查给定的设备是否存在，如果存在，返回True，否则返回False
        
        Args:
            device_path: 设备路径
            serial: 设备序列号
            两者必须至少提供一个，不能同时提供
        """
        if not device_path and not serial:
            raise ValueError("必须提供 device_path 或 serial 至少一个")
        
        if device_path and serial:
            raise ValueError("不能同时提供 device_path 和 serial")
        
        # 统一用序列号查数据库
        from database.models import DeviceModel
        
        # 如果传入的是路径，先获取序列号
        if device_path:
            serial = getSerial.get_serial(device_path)
            if not serial:
                return False
        
        # 用序列号查数据库
        device = DeviceModel.query.filter(DeviceModel.serial == serial).first()
        return device is not None

    def get_path(self, serial):
        """
        根据序列号获取设备路径，如果设备存在但没挂载，返回None
        """
        return serial_to_path(serial)

    def get_Serial(self, device_path):
        """
        根据设备路径获取序列号
        """
        return getSerial.get_serial(device_path)

    def get_capacity(self, device_path):
        """
        根据设备路径获取容量
        """
        return get_capacity(device_path)

    def get_device_role(self, device_path):
        """
        根据设备路径获取设备角色，指的是根据设备的类型，返回设备在卷中的角色，例如，是在zfs中作为一个raid参与者，还是作为一个单独的卷存在，
        """
        return None
    
# 模块级单例实例
device_manager = DeviceManager()

