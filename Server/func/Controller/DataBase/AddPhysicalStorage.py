import os
import sqlite3
import DataBase_pb2
from func.tools.DisKOperation import getDiskByPath, getDiskBySerialNumber, getMatchedDisk
from func.tools import _fileTime


def addPhysicalStorage(request,context):
    if request.diskInfo.kind in vars.kind["disk"]:
        return addDisk()
    else:
        AddDiskResult=DataBase_pb2.AddDiskResult()
        AddDiskResult.result="notSuchKind"
        return AddDiskResult
    
def addDisk(request):
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