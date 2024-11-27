import os
import sqlite3
import DataBase_pb2


def getDisk(request,context):
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