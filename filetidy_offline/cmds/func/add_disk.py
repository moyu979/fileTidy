from pathlib import Path
import sqlite3
import os
import logging

from cmds.tools.confs import conf
from cmds.tools.fileTime import fileTimeSecond
def add_disk():
    db_path=os.path.join(conf["data_path"],"data.db")
    if not os.path.exists(db_path):
        logging.warning("database not exist")
    else:
        conn=sqlite3.connect(db_path)
        cursor=conn.cursor()

        id=input("请输入磁盘序列号")
        add_time=fileTimeSecond()
        
        
        