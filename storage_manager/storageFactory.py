import sqlite3
import logging
import init_setting.conf as conf
from storage_manager.storage import Storage
class StorageFactory:
    """
    A factory class for creating storage instances.
    """

    @staticmethod
    def load_storage(id):
        conn=sqlite3.connect(conf.get("db_path"))
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
        return storage
    
    #通过路径自动读取存储设备信息，并存入数据库
    @staticmethod
    def init_by_path(path=None):
        pass
    
    #通过用户输入的数据给出一个存储设备，并且放到数据库
    @staticmethod
    def init_by_info(info=None):
        pass
    