

from datetime import datetime
import sqlite3
import os
from init_setting import conf
from volume_manager.volume import Volume
import volume_manager.volumeFactory as VolumeFactory
import file_manager.tools.Hash as Hash
class file:
    def __init__(self):
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

    def append_file(self):
        """
        根据已有的信息将文件写回数据库。
        """
        if self.volume is None:
            if self.abspath is None:
                raise ValueError("volume and path are None")
            else:
                volume:Volume.Volume=VolumeFactory.VolumeFactory.load_upper_volume(path=self.abspath)
                self.volume=volume.id
        print(VolumeFactory.VolumeFactory.load_volume_from_database(id=self.volume))

        self.now_path=self.abspath.replace(VolumeFactory.VolumeFactory.get_volume_path(self.volume),"")
        self.add_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn=sqlite3.connect(conf.get("db_path"))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        result=cursor.execute("SELECT * FROM File WHERE volume=? and now_path=?", (self.volume,self.now_path)).fetchall()
        
        if len(result)!=0:
            result=result[0]
            if conf.get("insert_node")=="relaxed":
                self.md5 = result["md5"]
                self.size = result["size"]
                self.add_time = result["add_time"]
                self.from_path = result["from_path"]
                self.now_path = result["now_path"]
                self.now_name = result["now_name"]
                self.volume = result["volume"]
                self.state = result["state"]
                self.info = result["info"]
            else:
                md5=Hash.getAHash(self.abspath)
                if md5==result["md5"]:
                    self.md5 = result["md5"]
                    self.size = result["size"]
                    self.add_time = result["add_time"]
                    self.from_path = result["from_path"]
                    self.now_path = result["now_path"]
                    self.now_name = result["now_name"]
                    self.volume = result["volume"]
                    self.state = result["state"]
                    self.info = result["info"]
                else:
                    self.md5=md5
                    self.size=os.path.getsize(self.abspath)
                    self.add_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.from_path=self.abspath
                    self.now_path=self.now_path
                    self.now_name=os.path.basename(self.abspath)
                    self.state="healthy"
                    self.info=""

                    conn=sqlite3.connect(conf.get("db_path"))
                    cursor = conn.cursor()
                    cursor.execute("UPDATE File SET state=? WHERE volume=? and now_path=?", (f"covered by {md5}",self.volume,self.now_path))
                    cursor.execute("INSERT INTO File (volume, now_path, md5, size, add_time, from_path, now_name, state, info) \
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", \
                                    (self.volume,self.now_path,md5,self.size,self.add_time,self.from_path,self.now_name,'healthy',self.info))
                    conn.commit()
                    conn.close()

        else:
            self.md5 = Hash.getAHash(self.abspath)
            self.size = os.path.getsize(self.abspath)
            self.add_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.from_path = self.abspath
            self.now_name = os.path.basename(self.abspath)
            self.state = "healthy"
            self.info = ""
            conn=sqlite3.connect(conf.get("db_path"))
            cursor = conn.cursor()
            cursor.execute("INSERT INTO File (volume, now_path, md5, size, add_time, from_path, now_name, state, info) \
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", \
                            (self.volume,self.now_path,self.md5,self.size,self.add_time,self.from_path,self.now_name,'healthy',self.info))
            conn.commit()
            conn.close()


            
            
            
                

