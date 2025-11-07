from component.device.device import Device
from component.device.tools import checkTape

class Tape(Device):
    def __init__(self, orm_model):
        super().__init__(orm_model)

    def check(self):
        checkTape(self.device_path)

    def set(self,key, value):
        super().set(key, value)