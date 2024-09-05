import grpc_protobuf.DataBase_pb2 as DataBase_pb2
import grpc_protobuf.DataBase_pb2_grpc as DataBase_pb2_grpc
import os
import sqlite3
from func import vars
from func.tools import _fileTime
from grpcServer.func.tools.DisKOperation import *
class DataBaseServicer(DataBase_pb2_grpc.DataBase):
    def InitDataBase(self,request,context):
        print(f"received InitDataBase request with {request.DataBasePath}")
        result=2
        result=initDataBase()
        return DataBase_pb2.InitAnswer(result=result,info=" ")
def initDataBase(path=None):
    vars.data["work_path"]=path
    if path==None:
        return initDataBase("./DataBase")
    else:
        print("Path:",path)
        if not os.path.exists(path):
            os.mkdir(path)
        db_path=os.path.join(path,"files.db")
        if os.path.exists(db_path):
            return 1
        conn=sqlite3.connect(db_path)
        cursor = conn.cursor()
        with open("./func/init.sql","r") as script:
            sql_script=script.read()
        cursor.executescript(sql_script)
        conn.close()
        return 0

def addDisk(name:str,disk_type:str,disk_path,kind_name):
    time:str=_fileTime.fileTimeSecond()

    for key,val in vars.kind:
        given_type:str=disk_type.lower()
        if name.startswith(key) and given_type not in val:
            return DataBase_pb2.addDiskResult(result=1,info="there might has a error on disktype, please check, if you are sure you are right, please use -f")
    
    disk_path=f"/dev/{name}"
    if not os.path.exists(disk_path):
         return DataBase_pb2.addDiskResult(result=3,info=f"disk in {disk_path} not found")
    size=get_Size(disk_path,disk_type)

    db_path=os.path.join(vars.data["work_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()

    # cursor.execute("INSERT INTO physicalStorage ")
    

        
    