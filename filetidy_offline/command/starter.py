import cmd
import os
import json
import sys
import logging

import core.tools.confs as confs
import core.component.add_file_info as add_file_info
import core.component.physical_storage as physical_storage

from core.func._init_db import init_db
from core.func._add_file import add_file
from core.func._add_disk import add_disk

import command.data_getter.get_add_file_info as get_add_file_info
import command.data_getter.get_physical_storage_data as get_physical_storage_data
class MyCmd(cmd.Cmd):
    def do_initDataBase(self,path=None):
        if path!="":
            logging.warning(f"your work path will be change from {confs.conf["data_path"]} to {path}")
            confs.conf["data_path"]=path
        init_db()

    def do_addFile(self,path=None):
        add_file_data,err=get_add_file_info.get_add_file_info()
        if err:
            logging.error(err)
            return
        _,err=add_file(add_file_data)
        if err:
            logging.error(err)
            return
        
    def do_addDisk(self,path=None):
        disk,err=get_physical_storage_data.get_physical_storage_data("disk")
        if err:
            logging.error(err)
            return
        
        _,err=add_disk(disk)
        if err:
            logging.error(err)
            return 
    def do_addTape(self,path=None):
        disk,err=get_physical_storage_data.get_physical_storage_data("tape")
        if err:
            logging.error(err)
            return
        
        _,err=add_disk(disk)
        if err:
            logging.error(err)
            return 

