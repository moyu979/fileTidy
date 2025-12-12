"""
单纯文件组合的卷
""" 
from component.volume.volume import Volume

class Consis(Volume):
    def __init__(self, orm_model=None,path=None):
        super().__init__(orm_model,path)

    def check(self):
        pass