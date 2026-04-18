"""
卷层抽象，用于管理卷，主要用于提供操作卷的抽象
"""
from abc import ABC
from apps.common.database.session import session_scope
from apps.common.database.models import FileModel
from apps.common.config.config import config_manager

class Volume(ABC):
    def __init__(self):
        self.orm_model = None      # 设备的数据对象
        self.device_path = None  # 设备的实际挂载路径，如果是None，说明这个设备没挂载
        self.in_database = False        # 设备是否在库，用于判断一些硬盘的属性
        self.files=None # 文件列表，用于管理文件
        

        
    def check(self):
        pass

    def set(self, key, value):
        pass

    def has_file(self, file_path):
        pass