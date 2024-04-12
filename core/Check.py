import sqlite3
import os
import sys

from _Hash import *
from _fileTime import *
from _Log import *
from _compareFile import *
from _removeFile import *
from _sizeManage import *

class Check:
    def __init__(self,db_path,files,check_file,check_log,hash) -> None:
        self.time=fileTime()

        self.file_path=os.path.abspath(files).replace("\\","/")
        self.db_path=db_path

        self.check_file=check_file 
        self.check_log=check_log
        self.check_hash=hash

        Log.open(db_path,self.time)
        Log.writeLog(f"Check --db {db_path} --files {files} --file {check_file} --log {check_log} --hash {self.check_hash}")
        
        database=os.path.join(db_path,"files.db")
        self.conn=sqlite3.connect(database)
        self.cur=self.conn.cursor()

        if self.file_path!="*":
            to_match=self.file_path+'%'
            self.traced_file=self.cur.execute("SELECT * FROM now WHERE path LIKE ?",(to_match,)).fetchall()
        else:
            self.traced_file=self.cur.execute("SELECT * FROM now",(to_match,)).fetchall()
            self.check_file==False

        if self.check_log:
            Log.writeLog("检查已经记录的")
            self.check_log_fun()

        if self.check_file:
            Log.writeLog("检查已有文件是否被记录")
            self.check_file_fun(self.file_path)

    def check_log_fun(self):
        count=0
        loss=0
        for i in self.traced_file:
            count=count+1
            if not os.path.exists(i[3]):
                loss=loss+1
                Log.writeLog(f"[traced file missing]\t{i[3]},{i[0]}")
        Log.writeLog("检查已经记录的 "+str(count)+" 文件,丢失跟踪 "+str(loss))

    def check_file_fun(self):
        count=0
        loss=0
        if self.checkhash:
            sizes=sizeManage(path)
        dic={}
        for i in self.traced_file:
            dic[i[2]]=i

        for root,dir,files in os.walk(path):
            for file in files:
                if file=="redirect.txt":
                    continue
                count=count+1
                path=os.path.join(root,file).replace("\\","/")
                if path in dic:
                    if self.checkhash:
                        hash=getAHash(path)
                        sizes.update(path)
                        sizes.showProgress()
                        if not hash==dic[path][1]:
                            Log.writeLog(f"[hash not match]\t{path},old:{dic[path][1]},new:{hash}")
                    
                else:
                    loss=loss+1
                    Log.writeLog(f"[file not traced]\t{path}")
        Log.writeLog("检查存在于文件夹中的 "+str(count)+" 文件,未被记录的有 "+str(loss))