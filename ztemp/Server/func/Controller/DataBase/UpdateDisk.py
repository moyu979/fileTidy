import os
import sqlite3

import DataBase_pb2


def updateDisk(request,context):
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