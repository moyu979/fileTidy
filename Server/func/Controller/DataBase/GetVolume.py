import os
import sqlite3
import DataBase_pb2

def getVolume(request,context):
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