import grpc_protobuf.DataBase_pb2 as DataBase_pb2
import grpc_protobuf.DataBase_pb2_grpc as DataBase_pb2_grpc
import os
import sqlite3
from func import vars
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

def add_physical_storage(name,kind="disk"):
    if kind=="disk":
        #如果是硬盘的话，存在无根情况，此时使用disk的唯一id标记其信息
        answer=os.popen(f"lsblk | grep {name}")
        lines=answer.read().split("\n")
        if len(lines)==1:
            return 1,"not such disk"
        elif len(lines)>2:
            return 2,"more than one disk has that name"

        datas=[x for x in lines[0].split(' ') if x]
        NAME=datas[0]
        SIZE=datas[3]
        MOUNTPOINTS=None
        if len(datas)>=7:
            MOUNTPOINTS=datas[6]
            #询问是否将标记加入

        
        
    elif kind in vars.tape:
        #如果是磁带的话，磁带不存在唯一的识别标志，因此需要特殊操作
        pass
