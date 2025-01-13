import cmd
import os
import json
import sys
import logging

import core.tools.confs as conf
import core.tools.fileTime as fileTime
from core.component.add_file_info import add_file_info

from core.func._init_db import init_db
from core.func._regist_hash import regist_hash
class MyCmd(cmd.Cmd):
    def do_initDataBase(self,path=None):
        if path!="":
            logging.warning(f"your work path will be change from {conf.conf["data_path"]} to {path}")
            conf.conf["data_path"]=path
        init_db()

    def do_addFile(self,path=None):
        path=input("please input file storage path")
        volume=input("please tell us which volume do you save your file")
        if volume=="":
            volume="0"
        data_pack=add_file_info()
        data_pack._file_path=path
        data_pack._storage_volume=volume

        rh=regist_hash()
        _,err=rh(data_pack)

        if err:
            print(err)


        

if __name__ == '__main__':
    MyCmd().cmdloop()