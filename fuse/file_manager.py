"""
文件管理器，用于管理文件的读写
"""

from functools import cache

class fileManager:
    """
    文件管理器，用于管理文件的读写
    """
    def __init__(self):
        self.file_path = "./file"
        self.file_method = "LRU"

    def readFile(self,path):
        if cacheManager.has(path):
            return cacheManager.get(path)
        else:
            return self.readFileFromDisk(path)
    
    def writeFile(self,path,data):
        # 将文件写入的功能，个人的考虑是轮询所有能写入的数据库
        # 首先，对含有磁带的数据库直接跳过
        # 在所有的硬盘数据库中，按照目录根由近到远，剩余容量由大到小的原则进行写入
        pass
    
    def has(self,path):
        return cacheManager.has(path)
    
    def get(self,path):
        return cacheManager.get(path)