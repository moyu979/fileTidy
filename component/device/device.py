"""
设备层抽象，用于管理硬件设备，主要用于提供操作硬件设备的抽象,包括：
- 硬盘
- 磁带
- TF卡
- 其他硬件设备

主要用于提供操作硬件设备的抽象
本文件是一个抽象层，具体的实现中drivers里 
"""

from tkinter import N


class Device:
    def __init__(self, orm_model=None,device_path=None):
        if orm_model is not None:
            self.orm_model = orm_model
            if device_path is not None:
                self.device_path = device_path
        else:
            self.orm_model = None
            if device_path is not None:
                self.device_path = device_path
            else:
                raise ValueError("device_path 和 orm_model 不能同时为空")

    def check(self):
        """
        用来检查介质的好坏，请注意，不是检查文件
        """
        pass

    def set(self,key, value):
        """
        用来设置介质的属性，会直接和数据库同步
        如果是设置路径，是个例外
        """
        pass



