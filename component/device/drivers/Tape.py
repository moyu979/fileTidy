from os import path
from component.device.device import Device
from component.device.tools import checkTape

class Tape(Device):
    def __init__(self, orm_model=None,path=None):
        super().__init__(orm_model,path)

    def check(self):
        checkTape(self.device_path)

    def set(self,key, value):
        super().set(key, value)