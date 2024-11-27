import os
import sqlite3
import DataBase_pb2


def updateVolume(request,context):
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
    