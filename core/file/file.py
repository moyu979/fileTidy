

from datetime import datetime
import json
import sqlite3
import os
from init_setting import conf
#import volume_manager.volumeFactory as VolumeFactory
import file_manager.tools.Hash as Hash
from file_manager.tools.Hash import getAHash

import logging
class File:
    def __init__(self,database_info=None):
        self.values={}
        if database_info is not None:
            self.values["md5"]=database_info[0]
            self.values["size"]=database_info[1]
            self.values["add_time"]=database_info[2]
            self.values["from_path"]=database_info[3]
            self.values["now_path"]=database_info[4]
            self.values["now_name"]=database_info[5]
            self.values["volume"]=database_info[6]
            self.values["state"]=database_info[7]
            self.values["info"]=database_info[8]
        else:
            self.abspath=None

            self.md5 = None
            self.size = None
            self.add_time = None
            self.from_path = None
            self.now_path = None
            self.now_name = None
            self.volume = None
            self.state = None
            self.info = None

    def set_volume(self,volume):
        """
        设置卷。
        :param volume: 卷id。
        """
        self.volume=volume

    def set_abspath(self,path):
        """
        设置文件的绝对路径。
        """
        self.abspath=os.path.abspath(path)

    def auto_complete(self):
        if self.volume is None:
            
            self.volume=VolumeFactory.VolumeFactory.get_volume_id(self.abspath)
            logging.debug(f"将volume重设为{self.volume}")

        if self.md5 is None:
            self.md5=getAHash(self.abspath)
        if self.size is None or self.size==-1:
            self.size = os.path.getsize(self.abspath)

        if self.add_time is None or self.add_time=="0000:00:00 00:00:00":
            self.add_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.now_path is None:
            self.now_path=self.abspath.replace(VolumeFactory.VolumeFactory.get_mount_point(self.volume),"")
            self.now_path=self.now_path.replace("datas\\","")

        if self.from_path is None:
            self.from_path=self.volume+":"+self.now_path

        if self.now_name is None:
            self.now_name= os.path.basename(self.abspath)

        if self.state is None:
            self.state="health"

        if self.info is None:
            self.info=""


    def to_dict(self):
        return {
            "abs_path":self.abspath,
            "md5":self.md5,
            "size":self.size,
            "add_time":self.add_time,
            "from_path":self.from_path,
            "now_path":self.now_path,
            "now_name":self.now_name,
            "volume":self.volume,
            "state":self.state,
            "info":self.info
        }
    # 将对象转换为 JSON 字符串
    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=4)
    
    def __str__(self):
        return self.to_json()
    
    def append_to_database(self):
        self.auto_complete()
        conn=sqlite3.connect(conf.get("db_path"))
        cursor = conn.cursor()

        cursor.execute("INSERT INTO File (md5,size,add_time,from_path,now_path,now_name,volume,state,info) VALUES (?,?,?,?,?,?,?,?,?)",
                       (self.md5,self.size,self.add_time,self.from_path,self.now_path,self.now_name,self.volume,self.state,self.info))
        conn.commit()
        conn.close()



            
            
            
                

