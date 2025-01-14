import os
import logging


from core.tools.confs import conf

from core.tools.db_tools import *
from core.tools.hash import get_hash
from core.tools.fileTime import fileTimeSecond
from core.tools.file import get_size
from core.tools.process import ProcessManage
from core.component.add_file_info import add_file_info

class add_file:
    def __init__(self):
        pass

    def __call__(self, file_path:add_file_info):
        _,err=check_db_existance()
        if err is not None:
            return _,err

        _,err=file_path.check()
        if err is not None:
            return _,err
        
        add_time,err=fileTimeSecond()
        if err:
            return None,err
        
        self.conn=sqlite3.connect(get_db_path())
        self.cursor=self.conn.cursor()

        process_manage=ProcessManage(file_path._file_path)
        for root,dir,files in os.walk(file_path._file_path):
            for file in files:

                path=os.path.join(root,file)
                # 获得哈希值
                hash,err=get_hash(path)
                if err:
                    self.conn.close()
                    return None,err
                #获得文件大小
                size,err=get_size(path)
                if err:
                    self.conn.close()
                    return None,err
                # 检查是否重复
                sent=f"SELECT * FROM files WHERE nowPath='{path}'"
                try:
                    data=self.cursor.execute(sent).fetchall()
                except Exception:
                    self.conn.close()
                    return None,f"executing {sent} error"
                # 如果这是一个全新文件
                if len(data)==0:
                    self.cursor.execute("INSERT INTO files (md5,size,addTime,fromPath,nowPath,nowName,storage,state,info) VALUES (?,?,?,?,?,?,?,?,?)",
                                     (hash,size,add_time,path,path,file,file_path._storage_volume,'',''))
                #如果记录过一个同路径文件
                else:
                    #如果这个文件哈希一样，说明是一个文件，跳过
                    if data[0][0]==hash:
                        continue
                    #如果哈希不一样，就冲突了，报错
                    else:
                        logging.warning(f"find a file has same path {path} \n but different md5 {hash} and {data[0][0]}")
                        self.conn.close()
                        return None,f"find a file has same path {path} \n but different md5 {hash} and {data[0][0]}"
                process_manage.update(path)
        self.conn.commit()
        self.conn.close()
        logging.debug("successful finished")
        return "success",None
        
