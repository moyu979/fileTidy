import os
import sqlite3
import logging
import core.component.check_file_data as check_file
from core.tools.db_tools import get_db_path
mode={
    "1":"check if all items in database exists",
    "2":"check if all files in dir logged",
    "0":"both 1 and 2"
}

class get_check_file_data:
    def __init__(self):
        self.check_file_data=check_file.check_file()

    def __call__(self, *args, **kwds):
        self.get_mode()
        self.get_check_path()
        self.get_check_volume()
        return self.check_file_data

    def get_mode(self):
        print("please tell us which mode (default 0)")
        for k,v in mode.items():
            print(k,v)

        self.check_file_data.mode=input()
        if self.check_file_data.mode=="":
            self.check_file_data.mode="0"
        if self.check_file_data.mode not in mode.keys():
            self.get_mode()

    def get_check_path(self):
        self.check_file_data.check_path=input("please tell us which dir stores those path:")
        if not os.path.exists(self.check_file_data.check_path):
            err="path not exist, retry"
            logging.error(err)
            self.get_check_path()
        self.check_file_data.check_path=os.path.abspath(self.check_file_data.check_path)

    def get_check_volume(self):
        self.check_file_data.check_volume=input("please tell us which volume you want to check:")
        self.conn=sqlite3.connect(get_db_path())
        self.cursor=self.conn.cursor()
        all_volume=self.cursor.execute("SELECT * FROM volume WHERE id=?",(self.check_file_data.check_volume,)).fetchall()
        if len(all_volume)==0:
            err="volume not exist, retry"
            logging.error(err)
            self.get_check_volume()