#todo 检查正确性


import sqlite3
import logging
import core.tools.db_tools as db
import core.component.add_volume_data as add_volume_data

def add_volume(volume:add_volume_data):
    volume.check()

    conn=sqlite3.connect(db.get_db_path())
    cursor=conn.cursor()
    print()
    try:
        cursor.execute("INSERT INTO Volume (id,addTime,lastCheck,volumeName,healthy,info,needAll,used,capacity,kind,isBase,globalPoint,format) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (volume.id,volume.add_time,volume.last_check,volume.volume_name,volume.health,volume.info,volume.need_all,volume.used,volume.capacity,volume.kind,volume.isBase,volume.global_point,volume.format))
        for a_sub,a_sub_dir in zip(volume.sub_id,volume.sub_dir):
            cursor.execute("INSERT INTO storageStructure (superid,subid,subdir,addTime,state,info) VALUES (?,?,?,?,?,?)",
                                (volume.id,a_sub,a_sub_dir,volume.add_time,volume.state,volume.info))
        
    except Exception:
        logging.error(str(Exception))
    finally:
        conn.commit()
        conn.close()
    

    
    return None,None