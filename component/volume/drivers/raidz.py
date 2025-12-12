"""
RAIDZ卷,基于zfs的raidz卷
"""
from component.volume.volume import Volume

class RAIDZ(Volume):
    def __init__(self, orm_model=None,path=None):
        super().__init__(orm_model,path)

    def check(self):
        pass