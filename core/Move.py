import sqlite3
import os
import sys

from _Hash import *
from _fileTime import *
from _Log import *
from _compareFile import *
from _removeFile import *
from _sizeManage import *

class Move:
    def __init__(self,db_path,src_path,dst_path) -> None:
        database_path=os.path.abspath(db_path).replace("\\","/")
        self.src_path=os.path.abspath(src_path).replace("\\","/")
        self.dst_path=os.path.abspath(dst_path).replace("\\","/")

        self.time=fileTime()

        Log.open(database_path)
        Log.writeLog(f"move --db {db_path} --source {src_path} --dest {dst_path}")

        database=os.path.join(db_path,"files.db")
        self.conn=sqlite3.connect(database)
        self.cur=self.conn.cursor()

        self.run()

        self.conn.commit()
        self.conn.close()
        
    def run(self):

        already_exist_dest_dict={}
        to_match=self.dst_path+"%"
        already_exist_in_dest=self.cur.execute("SELECT * FROM now WHERE path LIKE ?",(to_match,)).fetchall()
        for i in already_exist_in_dest:
            already_exist_dest_dict[i[2]]=i[0]

        already_exist_src_dict={}
        to_match=self.src_path+"%"
        already_exist_in_src=self.cur.execute("SELECT * FROM now WHERE path LIKE ?",(to_match,)).fetchall()
        for i in already_exist_in_src:
            already_exist_src_dict[i[1]]=i

        more_in_dest=[]
        for root,dir,files in os.walk(self.dst_path):
            for file in files:
                if file=="redirect.txt":
                    continue
                else:
                    file_path=os.path.join(root,file).replace("\\","/")
                    if file_path not in already_exist_dest_dict:
                        more_in_dest.append(file_path)

        Log.writeLog(f"find {len(more_in_dest)} unlogged files in dest")

        sizes=sizeManage(more_in_dest)

        for i in more_in_dest:
            hash=getAHash(i)
            if hash in already_exist_src_dict:
                self.cur.execute("UPDATE now SET time=?,path=? WHERE hashMd5=?",(self.time,i,hash))
                #todo 是否自动删除原本文件
            else:
                Log.writeLog(f"[no source file]\thash {already_exist_src_dict[hash][3]}")
            sizes.update(i)
            sizes.showProgress()



