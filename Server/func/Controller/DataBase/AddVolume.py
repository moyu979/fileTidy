import os
import sqlite3
import DataBase_pb2

import func.tools._fileTime as _fileTime

def addVolume(request,context):
    # 初始化结论
    AddVolumeResult=DataBase_pb2.AddVolumeResult()
    #加载数据库
    db_path=os.path.join(vars.data["db_path"],"files.db")
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()
    #初始化request
    request.volumeInfo.addTime=_fileTime.fileTimeSecond()
    request.volumeInfo.lastCheck="0000-00-00 00:00"
    if request.volumeInfo.healthy=="":
        request.volumeInfo.healthy='health'
    subs=request.subid
    #如果不存在卷名的话，直接出问题，因为在设计里卷名和
    if request.volumeInfo.volumeName=="":
        AddVolumeResult.result="nameNotGiven"
        return AddVolumeResult
    #试着写入数据库
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
