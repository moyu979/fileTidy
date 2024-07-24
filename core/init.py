import sqlite3
import os
import argparse
from _decorator import *

from _Log import *
class Init:
    @init_decorator
    def __init__(self,args) -> None:
        self.work_path=args.dbpath
        self.db_path=os.path.join(self.work_path,"files.db")

    @call_decorator
    def __call__(self):
        if not os.path.exists(self.work_path):
            os.mkdir(self.work_path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        with open("./core/Init.sql", 'r') as sql_file:
            sql_script = sql_file.read()
        cursor.executescript(sql_script)
        conn.close()

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dbpath",default="./db",help="dir path to store database")
    args = parser.parse_args()
    init=Init(args)
    init()