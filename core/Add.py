import sqlite3
import os
import argparse

from _decorator import *
from _fileTime import *
from _Hash import *
from _Log import *
from _processManage import *

class Add:
    @init_decorator
    def __init__(self,args) -> None:
        self.work_path=args.dbpath
        self.data_storage_path=args.datapath
        self.storageVirtual=args.dataStorage
        self.storagePhysical=args.datadisk
        self.addTime=None
        self.conn=None
        self.cur=None
        self.processManage=None

    @call_decorator
    def __call__(self):
        self.para_convert()
        for root,dir,files in os.walk(self.data_storage_path):
            for file in files:
                path=os.path.join(root,file)
                hash=getAHash(path)
                self.write_db(hash,path,file)
                self.processManage.update(path)
        self.conn.commit()
        self.conn.close()

    def para_convert(self):
        self.addTime=fileTime()
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

    def write_db(self,hash,path,name):
        size=get_size(path)
        self.cur.execute("INSERT INTO files (Md5,addTime,fromPath,nowPath,nowName,storageVirtual,storagePhysical,size) VALUES (?,?,?,?,?,?,?,?)",(hash,self.addTime,path,path,name,self.storageVirtual,self.storagePhysical,size))


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dbpath",default="./db",help="dir path to store database")
    parser.add_argument("--datapath",default=None,help="file path to add")
    parser.add_argument("--dataStorage",default=None,help="volume to store files")
    parser.add_argument("--datadisk",default=None,help="disk to store files")
    args = parser.parse_args()
    add=Add(args)
    add()