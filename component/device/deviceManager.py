"""
设备管理器，用于管理设备实例
"""

from component.device.deviceFactory import DeviceFactory


class DeviceManager:
    """设备管理器，管理设备实例"""
    
    def __init__(self):
        self.devices = []
    
    def newDevice(self, device_path):
        """
        创建一个新设备
        """
        return DeviceFactory.createDevice(device_path)

    def getDevice(self, device_path):
        """
        获取设备实例,不太建议使用
        """
        return DeviceFactory.createDevice(device_path)   

    def setDevice(self, device_path):
        """
        设置设备实例,不太建议使用
        """
        pass

    def checkDevice(self, device_path):
        """
        检查设备的介质情况
        """
        pass

    def replaceDevice(self, device_path):
        """
        用一个设备替换掉另一个设备，主要用于设备出现问题时的替换
        """
        pass

    def exists(self, id):
        """
        检查给定的设备id是否存在，如果存在，返回True，否则返回False
        如果传入的是path，首先会通过path获取id
        """
        pass

    def get_path(self, device_path):
        """
        获取设备路径，如果设备存在但没挂载，返回None
        """
        pass

    def get_id(self, device_path):
        """
        获取设备路径，如果设备存在但没挂载，返回None
        """
        pass

# 模块级单例实例
device_manager = DeviceManager()

