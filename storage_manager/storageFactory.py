import sqlite3
import logging
import init_setting.conf as conf
from storage_manager.storage import Storage
class StorageFactory:
    """
    A factory class for creating storage instances.
    """
    # A dictionary to hold all used storage instances
    storages={

    }

    @classmethod
    def load_storage(cls,id):
        conn=sqlite3.connect(conf.get("db_path"))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Storage WHERE id=?", (id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result is None:
            logging.error(f"Storage with id {id} not found.")
            raise ValueError(f"Storage with id {id} not found.")
        
        storage = Storage()
        storage.set_storage(result)
        cls.storages[id]=storage
        return storage
    
    #通过路径自动读取存储设备信息，并存入数据库
    @staticmethod
    def init_by_path(path=None):
        logging.error("init disk by path not finished")
    
    #通过用户输入的数据给出一个存储设备，并且放到数据库
    @staticmethod
    def init_by_input(info=None):
        logging.error("init disk by input not finished")

    @classmethod
    def update_all_storage(cls):
        #将所有设备的信息更新到数据库
        for v in cls.storages.values():
            v.to_database()

    @classmethod
    def load_exist_disks(cls):
        #载入系统中挂载的全部disk
        logging.error("load_exist_disks not finished")
    
    