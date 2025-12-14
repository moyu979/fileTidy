"""
设备层抽象，用于管理硬件设备，主要用于提供操作硬件设备的抽象,包括：
- 硬盘
- 磁带
- TF卡
- 其他硬件设备

主要用于提供操作硬件设备的抽象
本文件是一个抽象层，具体的实现中drivers里 
"""
class Device:
    def __init__(self, orm_model=None,device_path=None):
        self.orm_model = orm_model      # 设备的数据对象
        self.device_path = device_path  # 设备的实际挂载路径，如果是None，说明这个设备没挂载
        self.in_database = False        # 设备是否在库，用于判断一些硬盘的属性


    def check(self):
        """
        用来检查介质的好坏，请注意，不是检查文件，而是类似smartctl的方法
        """
        pass

    def set(self, key, value):
        """
        用来设置介质的属性，会直接和数据库同步
        如果是设置路径，是个例外，如果不在数据库，写数据库的步骤就会被忽略
        """
        pass

    def to_database(self):
        """
        将设备的信息写入数据库,如果不存在，就新增，如果存在，就刷一遍数据库
        """
        pass



