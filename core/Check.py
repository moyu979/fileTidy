import sqlite3
import os
import sys

from _hash import *
from _fileTime import *
from _Log import *
from _compareFile import *
from _removeFile import *

class Check:
    def __init__(self,db_path,files,existed,traced,hash) -> None:
        self.time=fileTime()
        self.path=os.path.abspath(files).replace("\\","/")
        self.checkhash=hash

        Log.open(db_path,self.time)
        Log.writeLog(f"Check --db {db_path} --files {files} --existed {existed} --traced {traced} --hash {self.checkhash}")
        
        database=os.path.join(db_path,"files.db")
        self.conn=sqlite3.connect(database)
        self.cur=self.conn.cursor()

        to_match=self.path+'%'
        self.traced_file=self.cur.execute("SELECT * FROM now WHERE path LIKE ?",(to_match,)).fetchall()

        if existed:
            Log.writeLog("检查已经记录的")
            self.check_exist()
        if traced:
            Log.writeLog("检查已有文件是否被记录")
            self.check_traced(self.path)

    def check_exist(self):
        count=0
        loss=0
        for i in self.traced_file:
            count=count+1
            if not os.path.exists(i[3]):
                loss=loss+1
                Log.writeLog(f"[traced file missing]\t{i[3]},{i[0]}")
        Log.writeLog("检查已经记录的 "+str(count)+" 文件,丢失跟踪 "+str(loss))

    def check_traced(self,path):
        count=0
        loss=0
        if self.checkhash:
            sizes=sizeManage(path)
        dic={}
        for i in self.traced_file:
            dic[i[3]]=i

        for root,dir,files in os.walk(path):
            for file in files:
                
                if file=="redirect.txt":
                    continue
                count=count+1
                path=os.path.join(root,file).replace("\\","/")
                if path in dic:
                    if self.checkhash:
                        hash=getAHash(path)
                        if not hash==dic[path][1]:
                            Log.writeLog(f"[hash not match]\t{path},old:{dic[path][1]},new:{hash}")
                        sizes.update(path)
                        sizes.showProgress()
                else:
                    loss=loss+1
                    Log.writeLog(f"[file not traced]\t{path}")
        Log.writeLog("检查存在于文件夹中的 "+str(count)+" 文件,未被记录的有 "+str(loss))