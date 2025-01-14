import cmd
import os
import json
import sys
import logging
import core.tools.confs as confs
#from core.tools.confs import conf
import core.component.add_file_info as add_file_info
import core.component.physical_storage as physical_storage

from core.func._init_db import init_db
from core.func._add_file import add_file
from core.func._add_disk import add_disk
class MyCmd(cmd.Cmd):
    def do_initDataBase(self,path=None):
        if path!="":
            logging.warning(f"your work path will be change from {confs.conf["data_path"]} to {path}")
            confs.conf["data_path"]=path
        init_db()

    def do_addFile(self,path=None):
        path=input("please input file storage path:")
        volume=input("please tell us which volume do you save your file:")
        if volume=="":
            volume="0"
        data_pack=add_file_info()
        data_pack._file_path=path
        data_pack._storage_volume=volume

        rh=add_file()
        _,err=rh(data_pack)

        if err:
            print(err)

    def do_addDisk(self,path):
        disk=physical_storage.physical_storage()
        disk.id=input("please input disk id:")
        disk.add_time=input("please input disk add time, keep empty to auto generate:")
        disk.last_check=input("please input disk last check time, keep empty to auto generate:")
        disk.disk_name=input("please input disk name, could be empty:")
        disk.health=input(f"please input disk healthy,\ndefaut:healty,chose={confs.health}:")
        if disk.health in confs.health.keys():
            print("11111")
            disk.health=confs.health[disk.health]
        disk.capacity=input(f"please input disk capacity, default is 0:")
        disk.kind=input(f"please choose a disk kind, choice={confs.disk_kind}:")
        if disk.kind in confs.disk_kind.keys():
            disk.kind=confs.disk_kind[disk.kind]
        disk.info=input("does anything need to add?")

        _,err=add_disk(disk)
        if err:
            print(err)

    def do_addTape(self,path):
        disk=physical_storage.physical_storage()
        disk.id=input("please input disk id, could be empty for tape:")
        disk.add_time=input("please input disk add time, keep empty to auto generate:")
        disk.last_check=input("please input disk last check time, keep empty to auto generate:")
        disk.disk_name=input("please input disk name, could be empty:")
        disk.health=input(f"please input disk healthy,\ndefaut:healty,chose={confs.health}:")
        if disk.health in confs.health.keys():
            disk.health=confs.health[disk.health]
        disk.capacity=input(f"please input disk capacity, default is 0:")
        disk.kind=input(f"please choose a disk kind, choice={confs.tape_kind}:")
        if disk.kind in confs.tape_kind.keys():
            disk.kind=confs.tape_kind[disk.kind]
        disk.info=input("does anything need to add?")

        _,err=add_disk(disk)
        if err:
            print(err)



        

if __name__ == '__main__':
    print(confs.conf)
    confs.load_conf()
    try:
        MyCmd().cmdloop()
    except KeyboardInterrupt:
        print("stop")
    print(confs.conf)
    confs.save_conf()
