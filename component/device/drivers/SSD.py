from component.device.device import Device
from component.device.tools.checkSSD import checkSSD

class SSD(Device):
    def __init__(self, orm_model=None, path=None):
        super().__init__(orm_model, path)

    def check(self):
        checkSSD(self.device_path)

    def set(self,key, value):
        super().set(key, value)