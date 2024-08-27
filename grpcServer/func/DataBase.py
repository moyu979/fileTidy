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
