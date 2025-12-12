class cacheManager:
    """
    缓存管理器，用于管理缓存
    目前来看，根据一些面试给出的一些反馈，考虑使用队列化+字典索引的方式，记录文件的信息，
    """
    def __init__(self):
        self.cache = []
        self.cache_path = "./cache"
        self.cache_method = "LRU"



    def cache(self,md5):
        """
        将制定哈希值的文件存入缓存中
        """
        pass

    def free():
        """
        释放指定大小的缓存文件
        """
        pass
