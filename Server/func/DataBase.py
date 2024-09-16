import grpc_protobuf.DataBase_pb2 as DataBase_pb2
import grpc_protobuf.DataBase_pb2_grpc as DataBase_pb2_grpc
import os
import sqlite3
from func import vars
from func.tools import _fileTime
from Server.func.tools.DisKOperation import *
from func.tools.DisKOperation import *

class DataBaseServicer(DataBase_pb2_grpc.DataBase):
    def InitDataBase(self,request,context):
        print(f"received InitDataBase request with {request.DataBasePath}")
        result=initDataBase()
        return result
    
    def GetDisk(self,request,context):
        return GetDisk(request)
    
    def GetVolume(self,request,context):
        return GetVolume(request)

    def AddDisk(self,request,context):
        if request.diskInfo.kind in vars.kind["disk"]:
            return AddDisk(request)
        
    def AddVolume(self,request,context):
        return AddVolume(request)
    
    def UpdateDisk(self,request,context):
        return UpdateDisk(request)
    
    def UpdateVolume(self,request,context):
        return UpdateVolume(request)
    

def initDataBase():
    result=DataBase_pb2.InitAnswer()
    path="./DataBase"
    vars.data["work_path"]=path
    print("Path:",path)
    if not os.path.exists(path):
        os.mkdir(path)
    db_path=os.path.join(path,"files.db")
    if os.path.exists(db_path):
        result.result=1
        return result
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()
    with open("./func/init.sql","r") as script:
        sql_script=script.read()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    result.result=0
    result.info=f"init database in {path}"
    return result

def GetDisk(request):
    db_path=os.path.join(vars.data["work_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()
    # todo:检查disk的查询是否存在对应关键字
    queryResult=cursor.execute("SELECT * FROM Disk WHERE ?=? AND healthy!='removed'",(request.id,request.info)).fetchall()
    GetDiskResult=DataBase_pb2.GetDiskResult()
    if len(queryResult)==0:
        GetDiskResult.result="notSuchDisk"
        return GetDiskResult
    else:
        for i in queryResult:
            a_disk=DataBase_pb2.Disk()
            a_disk.id=i[0]
            a_disk.addTime=i[1]
            a_disk.lastCheck=i[2]
            a_disk.diskName=i[3]
            a_disk.healthy=i[4]
            a_disk.capacity=i[5]
            a_disk.diskKind=i[6]
            a_disk.info=i[7]
            GetDiskResult.diskinfo.append(a_disk)
        return GetDiskResult

def GetVolume(request):
    db_path=os.path.join(vars.data["work_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()
    # todo:检查disk的查询是否存在对应关键字
    queryResult=cursor.execute("SELECT * FROM Volume WHERE ?=? AND healthy!='removed'",(request.id,request.info)).fetchall()
    GetVolumeResult=DataBase_pb2.GetVolumeResult()
    if len(queryResult)==0:
        GetVolumeResult.result="notSuchVolume"
        return GetVolumeResult
    else:
        for i in queryResult:
            a_disk=DataBase_pb2.Volume()
            a_disk.id=i[0]
            a_disk.addTime=i[1]
            a_disk.lastCheck=i[2]
            a_disk.volumeName=i[3]
            a_disk.healthy=i[4]
            a_disk.info=i[5]
            a_disk.needAll=i[6]
            a_disk.used=i[7]
            a_disk.capacity=i[7]
            GetVolumeResult.voluneInfo.append(a_disk)
        return GetVolumeResult

def AddDisk(request):
    if request.diskInfo.healthy=="":
        request.diskInfo.healthy='health'

    db_path=os.path.join(vars.data["work_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()

    request.diskInfo.addTime=_fileTime.fileTimeSecond()
    request.diskInfo.lastCheck="0000-00-00 00:00"

    AddDiskResult=DataBase_pb2.__annotations__ddDiskResult()
    
    if request.diskPath=="" and request.diskInfo.id=="":
        AddDiskResult.result="DiskInfoMissing"
        AddDiskResult.info=f"can not locate disk with empty name and empty Serial Number"
        return AddDiskResult
   
    elif request.diskPath!="" and request.diskInfo.id!="":
        request.diskInfo.capacity=getMatchedDisk(request.diskPath,request.SerialNumber)
        if request.capacity==None and request.forceDo==False:
            AddDiskResult.result="PathSericalNotMatch"
            AddDiskResult.knownDiskInfo=request.SerialNumber
            AddDiskResult.info=f"disk in {request.diskPath} with SerialNumber {request.SerialNumber} not found"
            return AddDiskResult
        elif request.forceDo:
            AddDiskResult.result="PathSericalNotMatch"
            AddDiskResult.knownDiskInfo=request.SerialNumber
            AddDiskResult.info=f"disk in {request.diskPath} with SerialNumber {request.SerialNumber} not found"
            return AddDiskResult
        else:
            AddDiskResult.result="success"

            
    elif request.diskInfo.id=="":
        request.diskInfo.id,request.diskINfo.capacity=getDiskByPath(request.diskPath)
        if request.diskInfo.id==None:
            AddDiskResult.result="PathNotExist"
            AddDiskResult.knownDiskInfo=request.diskPath
            AddDiskResult.info=f"disk in {request.diskPath} not found"
            return AddDiskResult
        else:
            AddDiskResult.result="success"
        
    elif request.diskPath=="":
        temp_capacity=getDiskBySerialNumber(request.diskInfo.id)
        if not temp_capacity and request.capacity=="":
            AddDiskResult.result="MissingCapacity"
        elif not temp_capacity:
            AddDiskResult.result="UsingGivenCapacity"
        else:
            AddDiskResult.result="success"
            request.diskInfo.capacity=temp_capacity
    else:
        AddDiskResult.result="UnknownFailure"
        return AddDiskResult
    
    cursor.execute("INSERT INTO physicalStorage (id,addTime,lastCheck,diskName,healthy,capacity,kind,info) VALUES (?,?,?,?,?,?,?,?)",\
                   (request.diskInfo.id,request.diskInfo.addTime,request.diskInfo.lastCheck,request.diskInfo.diskName,request.diskInfo.healthy,request.diskInfo.capacity,request.diskInfo.kind,request.diskInfo.info))
    conn.commit()
    conn.close()  
    
    return AddDiskResult

def AddVolume(request):
    db_path=os.path.join(vars.data["work_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()

    request.volumeInfo.addTime=_fileTime.fileTimeSecond()
    request.volumeInfo.last_check="0000-00-00 00:00"

    subs=request.subid

    AddVolumeResult=DataBase_pb2.AddVolumeResult()

    if request.volumeInfo.volumeName=="":
        AddVolumeResult.result="nameNotGiven"
        return AddVolumeResult
    else:
        found=cursor.execute("SELECT * FROM virtualStorage WHERE volumeName=?",(request.volumeInfo.volumeName,)).fetchall()
        if len(found)>0:
            AddVolumeResult.result="nameAlreadyExist"
            return AddVolumeResult
        else:
            for i in subs:
                found=cursor.execute("SELECT * FROM storageStructure WHERE subid=?",(i,)).fetchall()
                if len(found)>0:
                    AddVolumeResult.result="diskAlreadyUsed"
                    AddVolumeResult=f"disk called {i} already used in other pool"
                    return AddVolumeResult
            cursor.execute("INSERT INTO virtualStorage (addTime,lastCheck,volumeName,healthy,info,needAll,used,capacity) VALUES (?,?,?,?,?,?,?,?)",\
                           (request.volumeInfo.addTime,request.volumeInfo.lastCheck,request.volumeInfo.volumeName,request.volumeInfo.healthy,request.volumeInfo.info,request.volumeInfo.needAll,request.volumeInfo.used,request.volumeInfo.capacity))
            result=cursor.execute("SELECT id FROM virtualStorage WHERE volumeName=?",(request.volumeName,)).fetchall()[0]
            for i in subs:
                cursor.execute("INSERT INTO storageStructure (superid,subid,addTime) VALUES (?,?,?)",(result,i,request.volumeInfo.addTime))
            conn.commit()
            conn.close()
            AddVolumeResult.result="success"
            return AddVolumeResult
        
#这个函数是为了更新硬盘使用的，并不是为了替换硬盘！替换硬盘请使用其他命令
def UpdateDisk(request):
    oldDisk=request.oldDisk
    newDisk=request.newDisk
    
    db_path=os.path.join(vars.data["work_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()

    result=DataBase_pb2.UpdateDiskResult
    old_disk=cursor.execute("SELECT * FORM Disk WHERE id=?",(old_disk.id)).fetchall()

    if len(old_disk)==0:
        result.result=1
        return result
    else:
        cursor.execute("UPDATE Disk SET id=?,diskName=?,healthy=?,capacity=?,kind=?,info=? where id=?",\
                       (newDisk.id,newDisk.diskName,newDisk.healthy,newDisk.capacity,newDisk.kind,newDisk.info,oldDisk.id))
        result.result=0
        return result
    
#这个函数是为了更新硬盘使用的，并不是为了替换硬盘！替换硬盘请使用其他命令
def UpdateVolume(request):
    oldVolume=request.oldVolume
    newVolume=request.newVolume
    
    db_path=os.path.join(vars.data["work_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()

    result=DataBase_pb2.UpdateVolumeResult
    old_volume=cursor.execute("SELECT * FORM Volume WHERE id=?",(old_volume.id)).fetchall()

    if len(old_volume)==0:
        result.result=1
        return result
    else:
        cursor.execute("UPDATE Volume SET id=?,volumeName=?,healthy=?,info=?,needAll=?,used=?,capacity=? where id=?",\
                       (newVolume.id,newVolume.volumeName,newVolume.healthy,newVolume.info,newVolume.needAll,newVolume.used,newVolume.capacity,oldVolume.id))
        result.result=0
        return result
    