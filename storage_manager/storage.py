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
        
def set_storage(self, info_dict):
    """
    根据 info_dict 的键值对设置存储对象的属性。
    :param info_dict: 包含存储对象属性的字典。
    """
    # 定义允许设置的属性
    allowed_keys = {"id", "name", "kind", "add_time", "last_check", "healthy", "capacity", "info"}
    
    for key, value in info_dict.items():
        if key in allowed_keys:
            setattr(self, key, value)  # 动态设置属性
        else:
            raise KeyError(f"Invalid key '{key}' in info_dict. Allowed keys are: {allowed_keys}")

    def set_storage_by_path(self, path):
        self.to_database()
        logging.error("set_storage_by_path not finished")

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

    def check_disk(self):
        # 检查磁盘的健康状态（全量扫描）
        logging.error("check_disk not finished")

    def monitor_health(self):
        # 实时监控磁盘健康状态（实时监控）
        logging.error("monitor_health not finished")

    def formate_disk(self):
        # 格式化磁盘
        logging.error("formate_disk not finished")

    

    def get_disk_usage(self):
        # 获取磁盘使用情况
        #import shutil
        #total, used, free = shutil.disk_usage("/")
        #return {"total": total, "used": used, "free": free}
        logging.error("get_disk_usage not finished")

        