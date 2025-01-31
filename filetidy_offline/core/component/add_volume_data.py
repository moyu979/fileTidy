# todo 检查正确性
import os
import logging
import sqlite3
import core.tools.confs as confs
from core.tools.db_tools import get_db_path
from core.tools import generater
class volume_data:
    def __init__(self):
        self.id=""
        self.add_time=""
        self.last_check=""
        self.volume_name=""
        self.health=""
        self.info=""
        self.need_all=""
        self.used=""
        self.capacity=""
        self.kind=""
        self.isBase="false"
        self.global_point="unknown"

        self.sub_id=[]
        self.sub_dir=[]
        self.state=""
        
    def check(self):
        return None,None



            
    def execute(self):
        self.conn=sqlite3.connect(get_db_path())
        self.cursor=self.conn.cursor()
        self.cursor.execute("INSERT INTO Volume (id,addTime,lastCheck,volumeName,healthy,info,needAll,used,capacity,kind,isBase,globalPoint) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            (self.id,self.add_time,self.last_check,self.volume_name,self.health,self.info,self.need_all,self.used,self.capacity,self.kind,self.isBase,self.global_point))
        for a_sub,a_sub_dir in zip(self.sub_id,self.sub_dir):
            self.cursor.execute("INSERT INTO storageStructure (superid,subid,subdir,addTime,state,info) VALUES (?,?,?,?,?,?)",
                                (self.id,a_sub,a_sub_dir,self.add_time,self.state,self.info))
        
        self.conn.commit()
        self.conn.close()

        return None,None

        

        
