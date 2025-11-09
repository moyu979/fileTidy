"""
设备管理器，用于管理设备实例
"""

from component.device.deviceFactory import DeviceFactory


class VolumeManager:
    """设备管理器，管理设备实例"""
    
    def __init__(self):
        self.devices = []
    

    def newVolume(self, device_path, volume_path):
        """
        创建一个新卷
        """
        pass

    def exists(self, device_path):
        """
        检查设备是否存在
        """
        pass

    def get_path(self, device_path):
        """
        获取设备路径，如果设备存在但没挂载，返回None
        """
        pass

    def get_id(self, volume_path,strict=False):
        """
        获取卷id，如果卷存在但没挂载，返回None
        strict：
            为True时，会严格要求给出的路径是卷的挂载路径
            为False时，会向上检查目录树，获得最近的卷id
        """
        pass



# 模块级单例实例
volume_manager = VolumeManager()

