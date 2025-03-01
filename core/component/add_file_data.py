import os
import logging
import sqlite3

from core.tools.confs import conf
from core.tools.confs import *
from core.tools.db_tools import *

from core.tools.process import ProcessManage

from core.tools.hash import get_hash
from core.tools.generater import fileTimeSecond
from core.tools.file import get_size

class file_data:
    def __init__(self,file_path=None,storage_volume="0"):
        # 要导入的文件所在的目录
        self.file_path=None
        # 要导入的文件存在哪个卷内
        self.volume=None
        #这个目录应该被挂载在哪里
        #来自的卷会由这个目录下的目录和挂载点拼接而成
        self.root_point:str=None
        #这个目录会被存到volume中的哪里
        #volumePath会由原始的卷和这个值拼接而成
        self.volume_point=""
        #认为这个目录应该被存到哪里
        #showpath会由原始的卷和这个值拼接而成
        self.mount_point=None

    def check(self):
        if self.mount_point is None:
            err="mount_point not given"
            logging.error(err)
            return None,err

        if not os.path.exists(self.mount_point):
            err=f"{self.mount_point} not exist"
            logging.error(err)
            return err 

        if self.mount_point.startswith("./"):
            t=self.mount_point
            self.mount_point=os.path.abspath(self.mount_point)
            logging.debug(f"change path {t} to abs path {self.mount_point}")
        self.mount_point.replace("\\\\","/")
        self.mount_point.replace("\\","/")
        if self.mount_point.endswith("/"):
            self.mount_point=self.mount_point[:-1]

        self._file_path=os.path.abspath(self._file_path)

        if not self._file_path.startswith(self.mount_point):
            err=f"it seems you give a file path not in volume {self._storage_volume}, mount point is {self.mount_point}"
            logging.error(err)
            return None,err



        self.conn=sqlite3.connect(get_db_path())
        self.cursor=self.conn.cursor()

        # 要记录的目录是否存在
        if not os.path.exists(self._file_path):
            logging.warning(f"path {self._file_path} not exists")
            return None,f"path {self._file_path} not exists"
        
        #登记的卷是否存在于数据库
        volume=self.cursor.execute("SELECT isBase FROM Volume WHERE id=?",(self._storage_volume,)).fetchall()
        if volume is None:
            logging.error("not such volume")
            return None,"not such volume"

        if volume[0]=='false' :
            logging.error("not base storage")
            return None,"not base storage"

            
        return True,None


        
        
        
