import sqlite3
from core.storage.storage import Storage
import core.conf.conf as conf


def get_storage_from_db(storage_id):
    """
    从数据库中获取序列号为storage_id的磁盘记录，如果不存在则返回None
    """
    connect = sqlite3.connect(conf.get("db_path"))
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    res = cursor.execute("SELECT * FROM storages where id=?", (storage_id,)).fetchone()
    connect.commit()
    connect.close()

    if res is None:
        return None
    else:
        storage = Storage(res)
        storage.set_value("in_db", True)
        return storage


def get_all_indb_storage() -> list[Storage]:
    connect = sqlite3.connect(conf.get("db_path"))
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    res = cursor.execute("SELECT * FROM storages").fetchall()
    connect.commit()
    connect.close()

    result = []
    for r in res:
        storage = Storage(r)
        storage.set_value("in_db", True)
        result.append(storage)
    return result
