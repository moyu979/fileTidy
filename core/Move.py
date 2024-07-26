import sqlite3
import os
import argparse

from _decorator import *
from _fileTime import *
from _Hash import *
from _Log import *
from _processManage import *

class Move:
    @init_decorator
    def __init__(self,args) -> None:
        self.work_path=os.path.abspath(args.dbpath)
        self.from_path=os.path.abspath(args.frompath)
        self.to_path=os.path.abspath(args.topath)

        self.storageVirtual=args.dataStorage
        self.storagePhysical=args.datadisk

        self.conn=None
        self.cur=None
        self.processManage=None
    @call_decorator
    def __call__(self, *args: os.Any, **kwds: os.Any) -> os.Any:
        self.para_convert()
        to_check=self.from_path+"%"
        datas=self.cur.execute("SELECT (Md5,nowPath) FROM files WHERE nowPath like ?",(to_check,)).fetchall()
        data_dic={}
        for data in datas:
            data_dic[data[0]]=data[1]

        for root,dir,files in os.walk(self.data_storage_path):
            for file in files:
                path=os.path.join(root,file)
                hash=getAHash(path)

                before_path=data_dic.get(hash)
                if before_path==None:
                    Log.writeLog(f"[file not fount]\thash:{hash}\tpath:{path}")
                else:
                    self.cur.execute("UPDATE files SET nowPath=? WHERE Md5=? AND nowPath=?",(path,hash,before_path))
                data_dic.pop(path)
                self.processManage.update(path)

        chosen=input("there are still some not moved files, do you want to show them in log?(Y/N)")
        while chosen!="Y" and chosen!="N":
            chosen=input("there are still some not moved files, do you want to show them in log?(Y/N)")
                    
        if chosen!="N":
            return
        else:
            for key in data_dic.keys():
                Log.writeLog(f"[file not move]\thash:{data_dic[key]}\tpath:{key}")

    def para_convert(self):
        self.addTime=fileTime()
        self.conn=sqlite3.connect(os.path.join(self.work_path,"files.db"))
        self.cur=self.conn.cursor()

        #如果提供了磁盘信息，可以根据磁盘信息推断出校验组信息
        if self.storagePhysical!=None:
            res=self.cur.execute("SELECT * FROM physicalStorage where volumeName=?",(self.storagePhysical,)).fetchall()[0]
            
            self.storagePhysical=res[0]
            res=self.cur.execute("SELECT * FROM storageStructure where subid=?",(self.storagePhysical,)).fetchall()[0]
            storageVirtual=res[0]

            if self.storageVirtual!=None:
                res=self.cur.execute("SELECT * FROM virtualStorage where volumeName=?",(self.storageVirtual,)).fetchall()[0]
                if res[0]==storageVirtual:
                    self.storageVirtual=storageVirtual
                else:
                    raise Exception("info not match")
            else:
                self.storageVirtual=storageVirtual
        else:
            if self.storageVirtual==None:
                self.storageVirtual="referToDownloadVolumn"
            res=self.cur.execute("SELECT * FROM virtualStorage where volumeName=?",(self.storageVirtual,)).fetchall()[0]
            self.storageVirtual=res[0]
            self.storagePhysical=0