import cmd
import os
import json
import sys
from pathlib import Path
import logging

import core.tools.confs as confs
import core.component.add_file_data as add_file_data
import core.component.add_device_data as add_device_data


from core.func.init_db import init_db
from core.func.add_device import add_disk
from core.func.add_volume import add_volume
from core.func.add_file import add_file
from core.func.check_file import check_file

import command.data_getter.get_add_file_data as get_add_file_data
import command.data_getter.get_device_data as get_device_data
import command.data_getter.get_volume_data as get_volume_data
import command.data_getter.get_check_file_data as get_check_file_data
class MyCmd(cmd.Cmd):
    def do_initDataBase(self,path=None):
        if path!="":
            #logging.warning(f"your work path will be change from {confs.conf["data_path"]} to {path}")
            confs.conf["data_path"]=path
        init_db()
        
    def do_addDisk(self,path=None):
        data_gatter=get_device_data.get_device_data("disk")
        disk=data_gatter()
        add_disk(disk)
        
    def do_addTape(self,path=None):
        data_gatter=get_device_data.get_device_data("tape")
        tape=data_gatter()
        add_disk(tape)
        
    def do_addVolume(self,path=None):
        data_getter=get_volume_data.get_volume_data()
        volume=data_getter()

        add_volume(volume)

        
    def do_addFile(self,path=None):
        data_getter=get_add_file_data.get_add_file_data()
        add_file_data=data_getter()
        add_file(add_file_data)

    def do_checkFile(self,path=None):
        data_getter=get_check_file_data.get_check_file_data()
        check_file_data=data_getter()
        check_file(check_file_data)






        

