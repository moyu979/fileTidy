"""
设备管理器，用于管理设备实例
"""

from component.device.deviceFactory import DeviceFactory

class DeviceManager:
    def __init__(self):
        self.device_factory = DeviceFactory()
    def newDevice(self, device_path):
        """
        创建一个新设备
        """
        return self.device_factory.createDevice(device_path)
        
    def getDevice(self, device_path):
        """
        获取设备实例,不太建议使用
        """
        return self.device_factory.createDevice(device_path)   

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

