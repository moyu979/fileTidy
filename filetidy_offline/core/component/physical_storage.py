import logging
import sqlite3
import core.tools.db_tools as db
import core.tools.confs as confs
import core.tools.tape_tools as tape
import core.tools.fileTime as fileTime
import core.tools.db_tools as db
class physical_storage:
    def __init__(self):
        self.id=""
        self.add_time=""
        self.last_check=""
        self.disk_name=""
        self.health="health"
        self.capacity=""
        self.kind=""
        self.info=''

    def check(self):
        # 硬件id不存在的两种情况
        if self.id=="" and self.kind not in confs.tape_kind.values():
            logging.error("disk id not exist")
            return None,"disk id not exist"
        
        if self.id=="" and self.kind in confs.tape_kind.values():
            data,err=tape.get_a_tape_id()
            if err:
                return None,err
            logging.info(f"this tape will be name as {data}")
            self.id=data
        #id重复的情况
        data,err=db.db_execute(f"SELECT * FROM PhysicalStorage WHERE id='{self.id}'")
        if err:
            return None,err
        if len(data)!=0:
            logging.error("this disk already in database")
            return None,"this disk already in database"

        if self.add_time=="":
            self.add_time,err=fileTime.fileTimeSecond()
            if err:
                return None,err
        
        if self.last_check=="":
            self.last_check='0000:00:00 00:00:00'

        if self.capacity=="":
            self.capacity=0

        if self.kind=="":
            logging.error("unknown disk kind")
            return None,"unknown disk kind"
        
        return None,None
        
    def add_to_db(self):
        conn=sqlite3.connect(db.get_db_path())
        cursor=conn.cursor()
        cursor.execute("INSERT INTO PhysicalStorage (id,addTime,lastCheck,diskName,healthy,capacity,kind,info) VALUES (?,?,?,?,?,?,?,?)",
                       (self.id,self.add_time,self.last_check,self.disk_name,self.health,self.capacity,self.kind,self.info))
        conn.commit()
        conn.close()
        return None,None
    



        
