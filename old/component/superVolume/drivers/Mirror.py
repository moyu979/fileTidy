"""
镜像 SuperVolume，用于实现完全复制，类似 RAID1 的情况
通过完全复制提供数据冗余和容错能力
"""
from component.superVolume.superVolume import SuperVolume

class Mirror(SuperVolume):
    pass

