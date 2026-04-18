"""
设备层抽象，用于管理硬件设备，主要用于提供操作硬件设备的抽象,包括：
- 硬盘
- 磁带
    - lto5
    - lto6
- TF卡
- 其他硬件设备

主要用于提供操作硬件设备的抽象
本文件是一个抽象层，具体的实现中drivers里 
"""
from abc import ABC
from apps.common.database.session import session_scope


class Device(ABC):
    def __init__(self):
        self.orm_model = None      # 设备的数据对象
        self.device_path = None  # 设备的实际挂载路径，如果是None，说明这个设备没挂载
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
        if key == "path":
            self.device_path = value
            return

        attribute_map = {
            "path": (self, "device_path"),            "serial": (self.orm_model, "serial"),
            "name": (self.orm_model, "name"),
            "kind": (self.orm_model, "kind"),
            "add_time": (self.orm_model, "add_time"),
            "last_check_time": (self.orm_model, "last_check_time"),
            "capacity": (self.orm_model, "capacity"),
            "info": (self.orm_model, "info"),
        }
        
        if key not in attribute_map:
            raise ValueError(f"Invalid key: {key}. Valid keys are: {', '.join(attribute_map.keys())}")
        
        # 设置属性值
        target_obj, attr_name = attribute_map[key]
        setattr(target_obj, attr_name, value)
        
        # 同步到数据库
        with session_scope() as session:
            session.commit()



