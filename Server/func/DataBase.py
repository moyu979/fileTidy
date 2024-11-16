import grpc_protobuf.DataBase_pb2 as DataBase_pb2
import grpc_protobuf.DataBase_pb2_grpc as DataBase_pb2_grpc
import os
import sqlite3
from func import vars
from func.tools import _fileTime
from Server.func.tools.DisKOperation import *
from func.tools.DisKOperation import *
from func.tools.decorators import *
class DataBaseServicer(DataBase_pb2_grpc.DataBase):
    @say_begin_and_end
    def InitDataBase(self,request,context):
        print(f"received InitDataBase request with {"None" if request.DataBasePath == "" else request.DataBasePath}")
        result=initDataBase(request.DataBasePath)
        return result
    @say_begin_and_end
    def GetDisk(self,request,context):
        return GetDisk(request)
    @say_begin_and_end
    def GetVolume(self,request,context):
        return GetVolume(request)
    @say_begin_and_end
    def AddDisk(self,request,context):
        if request.diskInfo.kind in vars.kind["disk"]:
            return AddDisk(request)
        else:
            AddDiskResult=DataBase_pb2.AddDiskResult()
            AddDiskResult.result="notSuchKind"
            return AddDiskResult
    @say_begin_and_end    
    def AddVolume(self,request,context):
        return AddVolume(request)
    @say_begin_and_end
    def UpdateDisk(self,request,context):
        return UpdateDisk(request)
    @say_begin_and_end
    def UpdateVolume(self,request,context):
        return UpdateVolume(request)
    
#
def initDataBase(DBpath):
    result=DataBase_pb2.InitResult()
    if DBpath=="":
        path="./DataBase"
    else:
        path=DBpath
    vars.data["db_path"]=path
    if not os.path.exists(path):
        os.mkdir(path)
    db_path=os.path.join(path,"files.db")
    if os.path.exists(db_path):
        result.result="dataBaseAlreadyExist"
        return result
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()
    with open("./func/init.sql","r") as script:
        sql_script=script.read()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    result.result="success"
    result.info=f"init database in \"{path}\""
    return result

def GetDisk(request):
    GetDiskResult=DataBase_pb2.GetDiskResult()
    db_path=os.path.join(vars.data["db_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()
    sql=f"SELECT * FROM Disk WHERE {request.id}={request.info}"
    try:
        queryResult=cursor.execute(sql).fetchall()
    except Exception as e:
        GetDiskResult.result="DBFailure"
        GetDiskResult.info=e.args
        return GetDiskResult     
    
    if len(queryResult)==0:
        GetDiskResult.result="notSuchDisk"
        return GetDiskResult

    GetDiskResult.result="success"
    for i in queryResult:
        a_disk=DataBase_pb2.Disk()
        a_disk.id=i[0]
        a_disk.addTime=i[1]
        a_disk.lastCheck=i[2]
        a_disk.diskName=i[3]
        a_disk.healthy=i[4]
        a_disk.capacity=i[5]
        a_disk.kind=i[6]
        a_disk.info=i[7]
        GetDiskResult.diskinfo.append(a_disk)
    return GetDiskResult

def GetVolume(request):
    GetVolumeResult=DataBase_pb2.GetVolumeResult()

    db_path=os.path.join(vars.data["db_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()

    sql=f"SELECT * FROM Volume WHERE {request.id}={request.info}"
    try:
        queryResult=cursor.execute(sql).fetchall()
    except Exception as e:
        GetVolumeResult.result="DBFailure"
        GetVolumeResult.info=e.args
        return GetVolumeResult
    
    if len(queryResult)==0:
        GetVolumeResult.result="notSuchVolume"
        return GetVolumeResult
    GetVolumeResult.result="success"
    for i in queryResult:
        print(i)
        a_Volume=DataBase_pb2.Volume()
        a_Volume.id=str(i[0])
        a_Volume.addTime=i[1]
        a_Volume.lastCheck=i[2]
        a_Volume.volumeName=i[3]
        a_Volume.healthy=i[4]
        a_Volume.info=i[5]
        a_Volume.needAll=int(i[6])
        a_Volume.used=i[7]
        a_Volume.capacity=i[8]
        GetVolumeResult.volumeInfo.append(a_Volume)
    return GetVolumeResult

def AddDisk(request):
    if request.diskInfo.healthy=="":
        request.diskInfo.healthy='health'

    db_path=os.path.join(vars.data["db_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()

    request.diskInfo.addTime=_fileTime.fileTimeSecond()
    request.diskInfo.lastCheck="0000-00-00 00:00"

    AddDiskResult=DataBase_pb2.AddDiskResult()

    #add双空，也就是说没有任何手段获知到磁盘的sernial
    if request.diskPath=="" and request.diskInfo.id=="":
        AddDiskResult.result="DiskInfoMissing"
        AddDiskResult.info=f"can not locate disk with empty name and empty Serial Number"
        return AddDiskResult
    
    #如果两个都不为空，就要检查一下两个是否一致
    elif request.diskPath!="" and request.diskInfo.id!="":
        temp=request.diskInfo.capacity
        request.diskInfo.capacity=getMatchedDisk(request.diskPath,request.SerialNumber)
        #这个是不匹配情况
        if request.capacity==None and request.forceDo==False:
            AddDiskResult.result="PathSericalNotMatch"
            AddDiskResult.knownDiskInfo=request.SerialNumber
            AddDiskResult.info=f"disk in {request.diskPath} with SerialNumber {request.SerialNumber} not found"
            return AddDiskResult
        #这个是强制情况,如果路径和序列号不匹配，认为给出的路径无效，强制使用给出的信息
        elif request.capacity==None and request.forceDo:
            request.diskInfo.capacity=temp
            AddDiskResult.result="PathSericalNotMatchButForce"
            AddDiskResult.knownDiskInfo=request.SerialNumber
            AddDiskResult.info=f"disk in {request.diskPath} with SerialNumber {request.SerialNumber} not found"
        #如果全匹配上了，自然使用计算机获得的
        else:
            AddDiskResult.result="success"

     #如果没给id，但是给了path，就强行使用path       
    elif request.diskInfo.id=="" and request.diskPath!="":
        print(f"here is an no id but given path disk where path={request.diskPath}")
        request.diskInfo.id,request.diskInfo.capacity=getDiskByPath(request.diskPath)
        print(request.diskInfo.id,request.diskInfo.capacity)
        if request.diskInfo.id==None or request.diskInfo.id=="":
            AddDiskResult.result="PathNotExist"
            AddDiskResult.knownDiskInfo=request.diskPath
            AddDiskResult.info=f"disk in {request.diskPath} not found"
            return AddDiskResult
        else:
            AddDiskResult.result="success"
    #如果给了id，没给路径，直接记录    
    elif request.diskPath=="" and request.diskInfo.id!="":
        print(f"here is an no path but given id disk where id={request.diskInfo.id}")
        temp_capacity=getDiskBySerialNumber(request.diskInfo.id)
        if not temp_capacity and request.diskInfo.capacity=="":
            AddDiskResult.result="MissingCapacity"
        elif not temp_capacity:
            AddDiskResult.result="UsingGivenCapacity"
        else:
            AddDiskResult.result="success"
            request.diskInfo.capacity=temp_capacity
    try:
        cursor.execute("INSERT INTO Disk (id,addTime,lastCheck,diskName,healthy,capacity,kind,info) VALUES (?,?,?,?,?,?,?,?)",\
                   (request.diskInfo.id,request.diskInfo.addTime,request.diskInfo.lastCheck,request.diskInfo.diskName,request.diskInfo.healthy,request.diskInfo.capacity,request.diskInfo.kind,request.diskInfo.info))
    except Exception as e:
        AddDiskResult.result="DBFailure"
        AddDiskResult.info=e.args
    finally:
        conn.commit()
        conn.close()  
    return AddDiskResult

def AddVolume(request):
    db_path=os.path.join(vars.data["db_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()

    request.volumeInfo.addTime=_fileTime.fileTimeSecond()
    request.volumeInfo.lastCheck="0000-00-00 00:00"

    if request.volumeInfo.healthy=="":
            request.volumeInfo.healthy='health'

    subs=request.subid

    AddVolumeResult=DataBase_pb2.AddVolumeResult()
    if request.volumeInfo.volumeName=="":
        AddVolumeResult.result="nameNotGiven"
        return AddVolumeResult
    try:
        cursor.execute("INSERT INTO Volume (addTime,lastCheck,volumeName,healthy,info,needAll,used,capacity) VALUES (?,?,?,?,?,?,?,?)",\
                        (request.volumeInfo.addTime,request.volumeInfo.lastCheck,request.volumeInfo.volumeName,request.volumeInfo.healthy,request.volumeInfo.info,request.volumeInfo.needAll,request.volumeInfo.used,request.volumeInfo.capacity))
    except Exception as e:
        print(e)
        AddVolumeResult.result="DBFailure"
        AddVolumeResult.info=e.args
        return AddVolumeResult     
    result=cursor.execute("SELECT id FROM Volume WHERE volumeName=?",(request.volumeInfo.volumeName,)).fetchall()[0][0]
    for i in subs:
        if cursor.execute("SELECT * FROM Disk WHERE id=? AND healthy NOT ?",(i,"removed")).fetchall().shape[0]==0:
            AddVolumeResult.result="diskNotExist"
            return AddVolumeResult
        try:
            cursor.execute("INSERT INTO storageStructure (superid,subid,addTime) VALUES (?,?,?)",(result,i,request.volumeInfo.addTime))
        except Exception as e:
            print(e)
            AddVolumeResult.result="DBFailure"
            AddVolumeResult.info=e.args
            return AddVolumeResult
    conn.commit()
    conn.close()
    AddVolumeResult.result="success"
    return AddVolumeResult
        
#这个函数是为了更新硬盘使用的，并不是为了替换硬盘！替换硬盘请使用其他命令
def UpdateDisk(request):
    oldDisk=request.oldDisk
    newDisk=request.newDisk
    
    db_path=os.path.join(vars.data["db_path"],"files.db")
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
    
    db_path=os.path.join(vars.data["db_path"],"files.db")
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
    