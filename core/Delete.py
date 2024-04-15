import sqlite3
import os
import sys

from _Hash import *
from _fileTime import *
from _Log import *
from _compareFile import *
from _removeFile import *
from _sizeManage import *

class Delete:
    def __init__(self,db_path,removed_path) -> None:
        self.time=fileTime()

        self.db_path=db_path
        self.file_path=os.path.abspath(removed_path).replace("\\","/")

        Log.open(db_path,self.time)
        Log.writeLog(f"Delete --db {db_path} --files {removed_path}")

        database=os.path.join(db_path,"files.db")
        self.conn=sqlite3.connect(database)
        self.cur=self.conn.cursor()

    def __call__(self) -> os.Any:
        to_match=self.file_path+"%"
        files=self.cur.execute("SELECT * FROM now",(to_match,)).fetchall()
        hash_table={}
        for i in files:
            hash_table[i[1]]=i

        sizes=sizeManage(self.file_path)

        for root,dir,files in os.walk(self.file_path):
            for file in files:
                if file=="redirect.txt":
                    continue
                path=os.path.join(root,file).replace("\\","/")
                hash=getAHash(path)
                if not hash in hash_table:
                    Log.writeLog(f"[file not log]\t{path}")
                else:
                    old_path=hash_table[hash][2]
                    if os.path.exists(old_path):
                        Log.writeLog(f"[file exist]\t{path}\t{old_path}")
                    else:  
                        hash_table.pop(hash)
                        self.cur.execute("UPDATE now SET path=? where hashMd5=? AND path=?",("removed",hash,old_path))
                    sizes.update(path)
                    sizes.showProgress()