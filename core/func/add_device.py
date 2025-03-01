import sqlite3
import logging
import core.tools.db_tools as db
import core.component.add_device_data as add_device_data

def add_disk(disk:add_device_data.device_data):
    disk.check()

    conn=sqlite3.connect(db.get_db_path())
    cursor=conn.cursor()
    try:
        cursor.execute("INSERT INTO device (id,addTime,lastCheck,deviceName,healthy,capacity,kind,info) VALUES (?,?,?,?,?,?,?,?)",
                       (disk.id,disk.add_time,disk.last_check,disk.disk_name,disk.health,disk.capacity,disk.kind,disk.info))
    except Exception:
        logging.error(str(Exception))
    finally:
        conn.commit()
        conn.close()
