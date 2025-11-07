"""
设备工厂，用于创建和管理设备实例,同时提供对外接口
"""

from component.device.drivers.HDD import HDD
from component.device.drivers.SSD import SSD
from component.device.drivers.Tape import Tape

class DeviceFactory:
    def __init__(self):
        pass

    def createDevice(self, device_path):
        pass

    