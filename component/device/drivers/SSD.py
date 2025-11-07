from component.device.device import Device
from component.device.tools.linux import checkSSD

class SSD(Device):
    def __init__(self, orm_model):
        super().__init__(orm_model)

    def check(self):
        checkSSD(self.device_path)

    def set(self,key, value):
        super().set(key, value)