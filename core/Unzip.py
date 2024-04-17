import sqlite3
import os
import sys

from _Hash import *
from _fileTime import *
from _Log import *
from _compareFile import *
from _removeFile import *
from _sizeManage import *

class Unzip:
    def __init__(self,db_path,unzip_files) -> None:
        self.db_path=os.path.abspath(db_path).replace("\\","/")
        self.unzip_files=os.path.abspath(unzip_files).replace("\\","/")
        self.time=fileTime()

        Log.open(self.db_path)
        Log.writeLog(f"unzip --db {db_path} --unzip_files {unzip_files}")

        database=os.path.join(self.db_path,"files.db")
        self.conn=sqlite3.connect(database)
        self.cur=self.conn.cursor()

        self.unzip_datas=[]

        self.run()

        self.conn.commit()
        self.conn.close()

    def run(self):
        paths=os.listdir(self.unzip_files)
        for i in paths:
            p=os.path.join(self.unzip_files,i)
            self.get_a_zip_pair(p)

        self.find_all_in()