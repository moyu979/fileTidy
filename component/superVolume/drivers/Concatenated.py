"""
串联组合 SuperVolume，用于将两个 volume 东西组合的情况
组合起来才视作一个 volume，类似于 JBOD (Just a Bunch Of Disks)
"""
from component.superVolume.superVolume import SuperVolume

class Concatenated(SuperVolume):
    pass

