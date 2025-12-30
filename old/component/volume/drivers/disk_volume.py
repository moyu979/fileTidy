"""
单纯的硬盘卷，主要特征是能够进行一定的随机读写，因此可以删除，也可以添加文件
"""
import os
import shutil
from typing_extensions import override

from component.volume.volume import Volume


class DiskVolumes(Volume):
    def __init__(self, orm_model=None,path=None):
        super().__init__(orm_model,path)

    def check(self):
        pass

    @override
    def write(self, src_path, dst_path):
        shutil.copy(src_path, os.path.join(self.volume_path, "datas", dst_path))

    @override
    def get_file(self, src_path, dst_path):
        shutil.copy(os.path.join(self.volume_path, "datas", src_path), dst_path)
