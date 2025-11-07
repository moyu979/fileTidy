from tabnanny import check
from tkinter import NO
from component.device.device import Device
from component.device.tools.checkHdd import checkHdd
class HDD(Device):
    def __init__(self, orm_model=None,path=None):
        super().__init__(orm_model,path)


    def check(self):
        checkHdd(self.device_path)

    def set(self,key, value):
        super().set(key, value)

    