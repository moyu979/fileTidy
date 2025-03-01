import os
import logging
import sqlite3

import core.component.add_file_data as add_file_data
from core.tools.confs import conf
from core.tools.confs import *
from core.tools.db_tools import *

from core.tools.process import ProcessManage

from core.tools.hash import get_hash
from core.tools.generater import fileTimeSecond
from core.tools.file import get_size
def add_file(add_file_data:add_file_data.file_data):
    add_file_data.check()

    conn=sqlite3.connect(get_db_path())
    cursor=conn.cursor()

    origin_path=os.path.abspath(add_file_data.file_path).replace("\\\\","/").replace("\\","/")
    root_point=add_file_data.root_point.replace("\\\\","/").replace("\\","/")
    volume_point=add_file_data.volume_point.replace("\\\\","/").replace("\\","/")
    mount_point=add_file_data.mount_point.replace("\\\\","/").replace("\\","/")

    volume=add_file_data.volume
    process_manage=ProcessManage(origin_path)
    add_time=fileTimeSecond()

    for root,dir,files in os.walk(origin_path):
        for file in files:
            true_path=os.path.join(root,file).replace("\\\\","/").replace("\\","/")

            in_volume=true_path.replace(origin_path,"").replace("\\\\","/").replace("\\","/")

            file_from_path=(root_point+in_volume).replace("\\\\","/").replace("\\","/")
            file_volume_path=(volume_point+in_volume).replace("\\\\","/").replace("\\","/")
            file_show_path=(mount_point+in_volume).replace("\\\\","/").replace("\\","/")
            # hash=get_hash(path)
            size=get_size(true_path)

            data=cursor.execute("SELECT * FROM files WHERE storagePath=? and volume=?",(file_volume_path,volume)).fetchall()
            # try:
            #     data=cursor.execute("SELECT * FROM files WHERE storagePath=? and volume=?",(file_volume_path,volume)).fetchall()
            # except Exception:
            #         conn.close()
            #         print(f"executing {file_volume_path} error, {str(Exception)}")
            #         return None,f"executing {file_volume_path} error"
            
            # 如果这是一个全新文件,直接算哈希，并写入
            if len(data)==0:
                hash=get_hash(true_path)
                cursor.execute("INSERT INTO files (md5,size,state,info,addTime,fromPath,volume,storagePath,showPath) VALUES (?,?,?,?,?,?,?,?,?)",
                                (hash,size,"health","",add_time,file_from_path,volume,file_volume_path,file_show_path))
            else:
                 if conf["check_mode"]:
                    hash=get_hash(true_path)
                    if data[0][0]==hash:
                        continue
                    else:
                        logging.warning(f"find a file has same path {file_volume_path} \n but different md5 {hash} and {data[0][0]}")
                        conn.close()
                        raise Exception("hash not same")   
                 else:
                    pass
                 
            process_manage.update(true_path)

    conn.commit()
    conn.close()
    logging.debug("successful finished")
                  
        





