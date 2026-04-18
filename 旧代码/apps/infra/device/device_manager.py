import os
from apps.infra.device.os_adapter.path2serial import path2serial


class DeviceManager:
    def __init__(self):
        self.devices = []

    def get_device(self, device_id):
        return self.devices[device_id]

    def add_device(self, device):
        self.devices.append(device)

    def get_device_id(self, path):
        """
        根据路径获取设备id
        """
        device_id = input("暂时没想好怎么实现，请直接手动输入设备id: ").strip()
        if device_id == "":
            return None
        return device_id

    def get_device_path(self, device_id):
        """
        根据设备id获取路径
        """
        path = input("暂时没想好怎么实现，请直接手动输入路径: ").strip()
        if path == "":
            return None
        path = os.path.abspath(path)
        return path

device_manager = DeviceManager()
