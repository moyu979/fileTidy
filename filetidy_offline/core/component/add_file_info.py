import os
import logging
import sqlite3

from core.tools.confs import conf
from core.tools.confs import *
from core.tools.db_tools import *
class add_file_info:
    def __init__(self,file_path=None,storage_volume="0"):
        self._file_path=file_path
        self._storage_volume=storage_volume

    def check(self):
        self._file_path=os.path.abspath(self._file_path)
        # 要记录的目录是否存在
        if not os.path.exists(self._file_path):
            logging.warning(f"path {self._file_path} not exists")
            return None,f"path {self._file_path} not exists"
        #登记的卷是否存在于数据库
        data,err=db_execute(f"SELECT * FROM Volume WHERE id='{self._storage_volume}'")
        if err:
            return None,err
        
        if len(data)==0:
            logging.warning(f"volumn {self._storage_volume} not exist in data base")
            return False,f"volumn {self._storage_volume} not exist in data base"
            
        return True,None
    
        
        
        
        
