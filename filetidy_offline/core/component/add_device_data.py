import logging
import sqlite3
import core.tools.db_tools as db
import core.tools.db_tools as db
class device_data:
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
        self.conn=sqlite3.connect(db.get_db_path())
        self.cursor=self.conn.cursor()
        self.not_empty_checker()
        self.same_id_checker()
        self.conn.close()
        return None,None
    def not_empty_checker(self):
        if self.id=="":
            logging.error("disk id not exist")
            raise Exception("disk id not exist")
        if self.add_time=="":
            logging.error("add_time not given")
            raise Exception("add_time not given")
        if self.kind=="":
            logging.error("kind not given")
            raise Exception("kind not given")
        
    def same_id_checker(self):
        data=self.cursor.execute(f"SELECT * FROM device WHERE id='{self.id}'").fetchall()
        if len(data)!=0:
            logging.error("this disk already in database")
            raise Exception("this disk already in database")
        

    def execute(self):
        conn=sqlite3.connect(db.get_db_path())
        cursor=conn.cursor()
        cursor.execute("INSERT INTO device (id,addTime,lastCheck,diskName,healthy,capacity,kind,info) VALUES (?,?,?,?,?,?,?,?)",
                       (self.id,self.add_time,self.last_check,self.disk_name,self.health,self.capacity,self.kind,self.info))
        conn.commit()
        conn.close()
        return None,None
    



        
