import cmd
import os
import json
import sys
import logging

import cmds.tools.confs as conf
import cmds.tools.fileTime as fileTime
import cmds.func.init_db as init
class MyCmd(cmd.Cmd):
    def do_initDataBase(self,path=None):
        if path!="":
            logging.warning(f"your work path will be change from {conf.conf["data_path"]} to {path}")
            conf.conf["data_path"]=path
        init.init_db()

    def do_addTape():
        time=fileTime.fileTimeSecond()

if __name__ == '__main__':
    MyCmd().cmdloop()