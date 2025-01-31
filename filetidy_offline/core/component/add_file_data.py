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
        self.file_path=file_path
        self.storage_volume=storage_volume
        self.mount_point:str=None

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
    
    def execute(self):
        add_time=fileTimeSecond()
        
        conn=sqlite3.connect(get_db_path())
        cursor=conn.cursor()

        process_manage=ProcessManage(self.file_path)
        for root,dir,files in os.walk(self.file_path):
            for file in files:
                path=os.path.join(root,file)
                hash=get_hash(path)
                size,err=get_size(path)
                if err:
                    conn.close()
                    return None,err
                abs_pa=path
                path=path.replace(self.mount_point,"")
                path=path.replace("\\\\","/")
                path=path.replace("\\","/")
                sent=f"SELECT * FROM files WHERE nowPath='{path}'"
                try:
                    data=cursor.execute(sent).fetchall()
                except Exception:
                    conn.close()
                    return None,f"executing {sent} error"
                
                # 如果这是一个全新文件
                if len(data)==0:
                    cursor.execute("INSERT INTO files (md5,size,addTime,fromPath,nowPath,nowName,storage,state,info) VALUES (?,?,?,?,?,?,?,?,?)",
                                    (hash,size,add_time,path,path,file,self.storage_volume,'',''))

                #如果记录过一个同路径文件
                else:
                    #如果这个文件哈希一样，说明是一个文件，跳过
                    if data[0][0]==hash:
                        continue
                    #如果哈希不一样，就冲突了，报错
                    else:
                        logging.warning(f"find a file has same path {path} \n but different md5 {hash} and {data[0][0]}")
                        conn.close()
                        return None,f"find a file has same path {path} \n but different md5 {hash} and {data[0][0]}"
                process_manage.update(abs_pa)

        conn.commit()
        conn.close()
        logging.debug("successful finished")
        return "success",None

        
        
        
