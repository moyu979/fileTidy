import sqlite3
import logging
import core.conf.conf as conf
from core.storage.storage import Storage as Storage
from core.storage.storage_loader import get_storage_from_db
from .tools.getPhysicalDisks import get_physical_disks as get_physical_disks
from core.storage.storage_loader import get_storage_from_db
from core.storage.storage_loader import get_all_indb_storage
class StorageFactory:
    """
    A factory class for creating storage instances.
    """
    # A dictionary to hold all used storage instances
    storages:dict[str,Storage]={}

    @classmethod
    def load_all_storage(cls):
        """
            加载现有的全部分区,包括存在于数据库中的和不存在于数据库中的
        """
        cls.storages={}
        #加载在数据库中的
        in_dbs=get_all_indb_storage()
        for s in in_dbs:
            cls.storages[s.get_value("id")]=s

        #使用本机数据刷新数据库
        disks=get_physical_disks()
        for a_disk in disks:
            #如果在库，直接刷新
            if a_disk["id"] in cls.storages.keys():
                storage=cls.storages[a_disk["id"]]
                storage.set_value("kind",a_disk["type"])
                storage.set_value("capacity",a_disk["size"])
                storage.set_value("path",a_disk["device"])
            #如果不在库，直接新建
            else:
                #如果这个id不对应数据库中的磁盘
                disk=Storage()
                disk.set_value("id",a_disk["id"])
                disk.set_value("name","")
                disk.set_value("kind",a_disk["type"])
                disk.set_value("add_time","")
                disk.set_value("last_check","")
                disk.set_value("healthy","")
                disk.set_value("capacity",a_disk["size"])
                disk.set_value("info","0")
                disk.set_value("in_db",False)
                disk.set_value("path",a_disk["device"])
                cls.storages[disk.get_value("id")]=disk
        return cls.storages

    #尝试通过数据库加载指定id的磁盘，如不存在，则返回None
    @classmethod
    def load_storage_from_db(cls,id):
        """
            通过id加载从数据库中加载物理存储器，如果指定的id不存在于数据库中，返回None
        """
        storage=get_storage_from_db(id)
        if storage is not None:
            storage.set_value("in_db",True)
            cls.storages[storage.get_value("id")]=storage
        return storage
    
    @classmethod
    def get_cached_storage(cls):
        """
            获取全部已经缓存的存储器，不管是否存在于数据库中
        """
        return cls.storages
    
    @classmethod
    def get_all_mounted_storage(cls):
        """
            获得所有已经挂载的物理存储器，不论是否存在于数据库中
        """
        data=[]
        for k,storage in cls.storages.items():
            if storage.get_value("path") is not None:
                data.append(storage)
        return data
    
    @classmethod
    def add_disk_to_db(cls,id,name=None,info=None):
        """
            将指定的存储器添加到数据库中
        """
        for k,storage in cls.storages.items():
            if storage.get_value("id")==id:
                if storage.get_value("in_db"):
                    raise ValueError(f"storage with id {id} already in db")
                else:
                    if name is not None:
                        storage.set_value("name",name)
                    if info is not None:
                        storage.set_value("info",info)
                    storage.to_db()
                break

    @classmethod
    def get_storage(cls,id):
        """
            获取指定存储
        """
        return cls.storages.get(id,None)
    
    @classmethod
    def set_value(cls,id,k,v):
        cls.load_storage_from_db(id)
        if cls.storages.get(id,None) is None:
            logging.error(f"指定的id：{id}不存在对应的硬盘")
        else:
            cls.storages.get(id,None).set_value(k,v)

    @classmethod
    def flush(cls):
        for k,v in cls.storages.items():
            v.flush()

        



    
    