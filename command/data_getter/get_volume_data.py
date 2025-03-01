import logging
import sqlite3
import core.component.add_volume_data as add_volume_data
import core.tools.confs as confs
import core.tools.db_tools as db
from core.tools import generater

class get_volume_data:
    def __init__(self):
        self.volume=add_volume_data.volume_data()
    def __call__(self, *args, **kwds):
        self.conn=sqlite3.connect(db.get_db_path())
        self.cursor=self.conn.cursor()
        self.get_id()
        self.get_add_time()
        self.get_last_check()
        self.get_name()
        self.get_health()
        self.get_info()
        self.get_sub_volume()
        self.get_kind()
        self.get_format()

        self.get_need_all()
        self.get_used()
        self.get_capacity()

        self.get_is_base()
        
        self.get_state()
        self.get_mount_point()
        self.conn.commit()
        self.conn.close()
        return self.volume


    def get_id(self):
        self.volume.id=input("please tape in volume id, keep empty to generate automatically:")
        if self.volume.id=="":
            self.volume.id=generater.get_a_device_id()

    def get_add_time(self):
        self.volume.add_time=input("please input add time, it will be auto generated if keep empty:")
        if self.volume.add_time=="":
            self.volume.add_time=generater.fileTimeSecond()

    def get_last_check(self):
        self.volume.last_check=input("please input check time, it will be auto generated as never if keep empty:")
        if self.volume.last_check=="":
            self.volume.last_check="0000:00:00 00:00"

    def get_name(self):
        self.volume.volume_name=input("please tape in volume name, could be empty:")
        if self.volume.volume_name=="":
            self.volume.volume_name=None

    def get_health(self):
        print("please input disk healthy,default value is health:")

        for k,v in confs.device_health.items():
            print(f"\t{k},{v}")
        self.volume.health=input()
        if self.volume.health=="":
            self.volume.health="1"
        if self.volume.health in confs.device_health.keys():
            self.volume.health=confs.device_health[self.volume.health]
        if self.volume.health not in confs.device_health.values():
            err=f"unknown health state {self.volume.health},retry:"
            logging.error(err)
            self.get_health()

    def get_info(self):
        self.volume.info=input("please tape in detailed information, could be empty:")
    
    def get_sub_volume(self):
        sub_id=input("please tell us one sub id,(q to quit):")

        while sub_id!="q":
            data1=self.cursor.execute("SELECT * FROM volume WHERE id=?",(sub_id,)).fetchall()
            data2=self.cursor.execute("SELECT * FROM device WHERE id=?",(sub_id,)).fetchall()
            if len(data1)+len(data2)==0:
                logging.error(f"volume/device with id {sub_id} not exist, please type a new id:")
                sub_id=input()
                continue
            sub_dir=input("this volume use which volume as storage?(default is all disk):")
            self.volume.sub_id.append(sub_id)
            self.volume.sub_dir.append(sub_dir)
            sub_id=input("please tell us one sub id,(q to quit):")
        #判定0
        if len(self.volume.sub_id)==0:
            raise Exception("no sub id")

        
    def get_kind(self):
        if len(self.volume.sub_id)==1:
            self.volume.kind="single_disk"
        else:
            print("please tell us volume kind:")
            for k,v in confs.raid_kind.items():
                print(k,v)
            self.volume.kind=input()
            if self.volume.kind in confs.raid_kind.keys():
                self.volume.kind=confs.raid_kind[self.volume.kind]
            if self.volume.kind not in confs.raid_kind.values():
                err=f"{self.volume.kind} not in raid kind"
                logging.error(err)
                self.get_kind()


    def get_need_all(self):
        if len(self.volume.sub_id)==1:
            self.volume.need_all="2"
        elif self.volume.kind in confs.need_all:
            self.volume.need_all="1"
        else:
            self.volume.need_all=input("does this volume needs all sub volume?(true/false):")
            if self.volume.need_all=='t' or self.volume.need_all=='true':
                self.volume.need_all="1"
            if self.volume.need_all=='f' or self.volume.need_all=='false':
                self.volume.need_all='2'
            else:
                err="not a bool"
                logging.error(err)
                self.get_need_all()

    def get_used(self):
        self.volume.used=input("you use how much?")

    def get_capacity(self):
        self.volume.capacity=input("this volume has how many space:")

    def get_is_base(self):
        self.volume.isBase=input("does this volume could use individuel?(true/false):")
        if self.volume.isBase=='t':
            self.volume.isBase='true'
        if self.volume.isBase=='f':
            self.volume.isBase='false'
        if self.volume.isBase not in confs.bool_mode:
            err="not a bool"
            logging.error(err)
            self.get_is_base()

    def get_format(self):
        print("please type in file system:")
        for k,v in confs.file_system.items():
            print(k,v)
        self.volume.format=input()
        if self.volume.format in confs.file_system.keys():
            self.volume.format=confs.file_system[self.volume.format]
        if self.volume.format not in confs.file_system.values():
            logging.error("file system not exists")
            self.get_format()


    def get_state(self):
        self.volume.state=input("does it in use?(default inuse):")
        if self.volume.state=="":
            self.volume.state="inuse"
        
    def get_mount_point(self):
        self.volume.global_point=input("please input global point,default point is \"/\":")
        if self.volume.global_point=="":
            self.volume.global_point="/"
