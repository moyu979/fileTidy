import os
import sqlite3

import grpc_protobuf.FileControl_pb2 as FileControl_pb2
import grpc_protobuf.FileControl_pb2_grpc as FileControl_pb2_grpc

from vars import *
from tools._fileTime import *
from tools._processManage import *
from tools._Hash import *
class FileControlServicer(FileControl_pb2_grpc.FileControl):    
    def AddFile(self,request,context):
        print(f"received request")
        addFile()
        return FileControl_pb2.AddFileAnswer(Result="success",info="none")
    
def addFile(storage_location):
    if not os.path.exists(file_path):
        return "FileNotExist",f"{file_path} not exist"
    file_path=os.path.abspath(file_path).replace("\\","/")

    work_path=vars.data["db_path"]
    db_path=os.path.join(work_path,"files.db")
    
    if not os.path.exists(db_path):
        return "DataBaseNotExist","DataBaseNotExist"
    conn=sqlite3.connect(os.path.join(db_path,"files.db"))
    cur=conn.cursor()

    addTime=fileTime()
    process=ProcessManage(file_path)

    storage=cur.execute("SELECT * FROM virtualStorage WHERE volumeName=?",(storage_location,)).fetchall()
    if storage[-1]!=1:
        return "NotMinimumStorage","The storage unit you have chosen is not the minimum storage unit. Please provide a more detailed storage location"
    
    for root,dir,files in os.walk(file_path):
        for file in files:
            path=os.path.join(root,file)
            hash=getAHash(path)
            size=get_size(path)
            cur.execute("INSERT INTO files (Md5,size,addTime,fromPath,nowPath,nowName,storageVirtual) VALUES (?,?,?,?,?,?,?)",\
                             (hash,size,addTime,path,path,file,storage_location))
            process.update(path)
    

    conn.commit()
    conn.close()



    
    
