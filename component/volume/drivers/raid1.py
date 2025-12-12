"""
镜像卷,基于zfs的raid1卷
"""
from component.volume.volume import Volume

class RAID1(Volume):
    def __init__(self, orm_model=None,path=None):
        super().__init__(orm_model,path)

    def check(self):
        pass