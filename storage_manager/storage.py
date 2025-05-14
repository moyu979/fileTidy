import sqlite3
import logging
import init_setting.conf as conf

class Storage:
    def __init__(self):
        self.id = None
        self.name = None
        self.kind = None

        self.add_time = None
        self.last_check = None
        
        self.healthy = None
        self.capacity = None

        self.info = None
        
    def set_storage(self, info_set):
        """
        根据 info_set 的值按顺序设置存储对象的属性。
        """
        if len(info_set) != 8:
            raise ValueError("info_set must contain exactly 8 elements.")
        
        self.id = info_set[0]
        self.name = info_set[1]
        self.kind = info_set[2]
        self.add_time = info_set[3]
        self.last_check = info_set[4]
        self.healthy = info_set[5]
        self.capacity = info_set[6]
        self.info = info_set[7]

    def to_database(self):
        conn=sqlite3.connect(conf.get("db_path"))
        cursor = conn.cursor()
        # 使用 INSERT OR REPLACE 实现存在更新，不存在插入
        cursor.execute("""
            INSERT INTO Storage (id, name, kind, addTime, lastCheck, healthy, capacity, info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                kind=excluded.kind,
                addTime=excluded.addTime,
                lastCheck=excluded.lastCheck,
                healthy=excluded.healthy,
                capacity=excluded.capacity,
                info=excluded.info
        """, (self.id, self.name, self.kind, self.add_time, self.last_check, self.healthy, self.capacity, self.info))
        
        conn.commit()
        conn.close()


