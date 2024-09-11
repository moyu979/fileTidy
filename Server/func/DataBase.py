import grpc_protobuf.DataBase_pb2 as DataBase_pb2
import grpc_protobuf.DataBase_pb2_grpc as DataBase_pb2_grpc
import os
import sqlite3
from func import vars
from func.tools import _fileTime
from Server.func.tools.DisKOperation import *
from tools.DisKOperation import *

class DataBaseServicer(DataBase_pb2_grpc.DataBase):
    def InitDataBase(self,request,context):
        print(f"received InitDataBase request with {request.DataBasePath}")
        result=initDataBase(request.path)
        return DataBase_pb2.InitAnswer(result=result,info=" ")
    def AddPhysicalStorage(self,request,context):
        if request.kind in vars.kind["disk"]:
            return addDisk(request)
        
    def AddVirtualStorage(self,request,context):
        return addVirtualStorage(request)

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

def addDisk(request):
    if request.healthy=="":
        request.healthy='health'

    db_path=os.path.join(vars.data["work_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()

    request["time"]=_fileTime.fileTimeSecond()
    request["last_check"]="0000-00-00 00:00"

    addDiskResult=DataBase_pb2.addDiskResult()
    
    if request.diskName=="" and request.SerialNumber=="":
        addDiskResult.result="DiskInfoMissing"
        addDiskResult.info=f"can not locate disk with empty name and empty Serial Number"
        return addDiskResult
   
    elif request.diskName!="" and request.SerialNumber!="":
        request.capacity=getMatchedDisk(request.diskPath,request.SerialNumber)
        if request.capacity==None:
            addDiskResult.result="PathSericalNotMatch"
            addDiskResult.knownDiskInfo=request.SerialNumber
            addDiskResult.info=f"disk in {request.diskPath} with SerialNumber {request.SerialNumber} not found"
            return addDiskResult
        else:
            addDiskResult.result="success"

            
    elif request.SerialNumber=="":
        request.SerialNumber,request.capacity=getDiskByPath(request.diskPath)
        if request.SerialNumber==None:
            addDiskResult.result="PathNotExist"
            addDiskResult.knownDiskInfo=request.diskPath
            addDiskResult.info=f"disk in {request.diskPath} not found"
            return addDiskResult
        else:
            addDiskResult.result="success"
        
    elif request.diskPath=="":
        temp_capacity=getDiskBySerialNumber(request.SerialNumber)
        if not temp_capacity and request.capacity=="":
            addDiskResult.result="MissingCapacity"
        elif not temp_capacity:
            addDiskResult.result="UsingGivenCapacity"
        else:
            addDiskResult.result="success"
            request.capacity=temp_capacity
    else:
        addDiskResult.result="UnknownFailure"
        return addDiskResult
    
    cursor.execute("INSERT INTO physicalStorage (id,addTime,lastCheck,diskName,healthy,capacity,kind,info) VALUES (?,?,?,?,?,?,?,?)",\
                   (request.id,request.addTime,request.lastCheck,request.diskName,request.healthy,request.capacity,request.kind,request.info))
            
    conn.commit()
    conn.close()  
    
def addVirtualStorage(request):
    db_path=os.path.join(vars.data["work_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()

    request["time"]=_fileTime.fileTimeSecond()
    request["last_check"]="0000-00-00 00:00"

    subs=request.subid

    addVirtualStorageResult=DataBase_pb2.addVirtualStorageResult()

    if request.name=="":
        addVirtualStorageResult.result="nameNotGiven"
        return addVirtualStorageResult
    elif len(cursor.execute("SELECT * FROM virtualStorage WHERE volumeName=?",(request.name,)).fetchall())>0:
        addVirtualStorageResult.result="nameAlreadyUsed"
        return addVirtualStorageResult
    else:
        found=cursor.execute("SELECT * FROM virtualStorage WHERE volumeName=?",(request.volumeName,)).fetchall()
        if len(found)>0:
            addVirtualStorageResult.result="nameAlreadyExist"
            return addVirtualStorageResult
        else:
            for i in subs:
                found=cursor.execute("SELECT * FROM storageStructure WHERE subid=?",(i,)).fetchall()
                if len(found)>0:
                    addVirtualStorageResult.result="diskAlreadyUsed"
                    addVirtualStorageResult=f"disk called {i} already used in other pool"
                    return addVirtualStorageResult
            cursor.execute("INSERT INTO virtualStorage (addTime,lastCheck,volumeName,healthy,info,needAll,used,capacity) VALUES (?,?,?,?,?,?,?,?)",\
                           (request["time"],request["last_check"],request.volumeName,request.healthy,request.info,request.capacity,request.needAll,request.used))
            result=cursor.execute("SELECT id FROM virtualStorage WHERE volumeName=?",(request.volumeName,)).fetchall()[0]
            for i in subs:
                cursor.execute("INSERT INTO storageStructure (superid,subid,addTime) VALUES (?,?,?)",(result,i,request["time"]))
            conn.commit()
            conn.close()
            addVirtualStorageResult.result="success"
            return addVirtualStorageResult
    addVirtualStorageResult.result="unknownError"
    return addVirtualStorageResult
def getDiskInfo(request):
    db_path=os.path.join(vars.data["work_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()

    result=cursor.execute("SELECT * FROM physicalStorage WHERE ?=? AND healthy!='removed'",(request.id,request.info)).fetchall()
    GetDiskInfoAnswerResult=DataBase_pb2.GetDiskInfoAnswer()
    if len(result)==0:
        GetDiskInfoAnswerResult.result="notSuchdisk"
        return GetDiskInfoAnswerResult
    elif len(result)>1:
        GetDiskInfoAnswerResult.result="tooMuchChoice"
        return GetDiskInfoAnswerResult
    else:
        GetDiskInfoAnswerResult.result="success"
        GetDiskInfoAnswerResult.diskinfo.SerialNumber=result[0][0]
        GetDiskInfoAnswerResult.diskinfo.addTime=result[0][1]
        GetDiskInfoAnswerResult.diskinfo.lastCheck=result[0][2]
        GetDiskInfoAnswerResult.diskinfo.diskName=result[0][3]
        GetDiskInfoAnswerResult.diskinfo.healthy=result[0][4]
        GetDiskInfoAnswerResult.diskinfo.capacity=result[0][5]
        GetDiskInfoAnswerResult.diskinfo.diskKind=result[0][6]
        GetDiskInfoAnswerResult.diskinfo.info=result[0][7]
        return GetDiskInfoAnswerResult
