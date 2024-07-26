import sqlite3
import os
import argparse

from _decorator import *
from _fileTime import *
from _Hash import *
from _Log import *
from _processManage import *

class CheckExistence:
    """
        检查某一个目录下的文件是否都被记录了
    """
    @init_decorator
    def __init__(self,args):
        self.work_path=os.path.abspath(args.dbpath)
        self.data_storage_path=os.path.abspath(args.datapath)
        self.storagePhysical=args.datadisk
        self.storageVirtual=args.dataStorage
        self.checkTime=None
        self.conn=None
        self.cur=None
        self.processManage=None



    @call_decorator
    def __call__(self):
        self.para_convert()
        to_check=self.data_storage_path+"%"
        datas=self.cur.execute("SELECT (Md5,nowPath) FROM files WHERE nowPath like ?",(to_check,)).fetchall()
        data_dic={}
        for data in datas:
            data_dic[data[1]]=data[0]

        for root,dir,files in os.walk(self.data_storage_path):
            for file in files:
                path=os.path.join(root,file)
                hash=getAHash(path)
                hash2=data_dic.get(path)

                if hash2==None:
                    Log.writeLog(f"[file not loged]\thash:{hash}\tpath{path}")
                elif hash2!=hash:
                    Log.writeLog(f"[file not match]\tbeforehash:{hash2}\tnowhash:{hash}\tpath:{path}")
                data_dic.pop(path)
                self.processManage.update(path)
        for k in data_dic.keys():
            Log.writeLog(f"[file not exist]\thash:{data_dic[k]}\tpath:{k}")
        self.conn.commit()
        self.conn.close()

    def para_convert(self):
        self.checkTime=fileTime()
        self.conn=sqlite3.connect(os.path.join(self.work_path,"files.db"))
        self.cur=self.conn.cursor()
        self.processManage=ProcessManage(self.data_storage_path)
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
    
