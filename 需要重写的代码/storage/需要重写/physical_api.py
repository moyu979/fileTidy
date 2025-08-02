import logging
import core.storage.storageFactory as storageFactory
import core.storage.tools.check_physical as _check


# 增加一个物理存储器
def add():
    pass


# 检查指定存储器是否可用
def check(id=None, path=None):
    if id is not None:
        physical = storageFactory.StorageFactory.get_storage_by_id()
    elif path is not None:
        physical = storageFactory.StorageFactory.get_storage_by_path()
    else:
        logging.error("未给出正确的函数，将不会进行校验")

    _check(physical)


# 检查指定存储器是否存在于指定的库中
def exist():
    pass


# 检查硬件磁盘阵列
def check_raid(id):
    pass
