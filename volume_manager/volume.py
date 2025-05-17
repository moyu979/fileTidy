from datetime import datetime
import json
import logging
import sqlite3

from init_setting import conf
from volume_manager.tools.id_generate import generate_id

class Volume:
    def __init__(self):
        self.id = None
        self.name = None
        self.capacity = None

        self.add_time = None
        self.last_check = None
        self.healthy = None
        self.info = None

        self.need_all=None

        self.storages = []

        self.mount_point = None

    def load_info(self, id:str=None, name:str=None):
        """通过给定的id或name加载卷的信息"""
        if id is not None or name is not None:
            logging.debug("load volume from database")
            conn=sqlite3.connect(conf.get("db_path"))
            cursor = conn.cursor()
            if id is not None:
                logging.debug("load volume from database by id")
                cursor.execute("SELECT * FROM Volume WHERE id=?", (id,))
            elif name is not None:
                logging.debug("load volume from database by name")
                cursor.execute("SELECT * FROM Volume WHERE name=?", (name,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result is None:
                logging.error(f"Volume with id {id} not found.")
                raise ValueError(f"Volume with id {id} not found.")

            self.id = result[0]
            self.name=result[1]
            self.capacity=result[2]
            self.add_time=result[3]
            self.last_check=result[4]
            self.healthy=result[5]
            self.info=result[6]
            self.need_all=result[7]
            self.used=result[8]

            conn=sqlite3.connect(conf.get("db_path"))
            cursor = conn.cursor()
            temp=cursor.execute("SELECT * FROM storageStructure WHERE superid=?", (self.id,)).fetchall()
            if len(temp)==0:
                logging.error(f"your volume {self.id} has no sub volume")
                raise ValueError(f"Volume with id {id} not found.")
            for i in temp:
                self.storages.append(i[1])
            cursor.close()
            conn.close()

    def new_volume(self, info_dict:dict=None):
        """
        根据 info_dict 的键值对设置卷对象的属性。
        :param info_dict: 包含卷对象属性的字典。
        """
        # 定义允许设置的属性
        now_time=datetime.now().strftime("%Y:%m:%d %H:%M:%S")

        self.id = info_dict.get("id", generate_id())
        self.name = info_dict.get("name", self.id)
        self.capacity = info_dict.get("capacity", 0)

        self.add_time = info_dict.get("add_time", now_time)
        self.last_check = info_dict.get("last_check", now_time)
        self.healthy = info_dict.get("healthy", "health")
        self.info = info_dict.get("info", "")
        self.need_all = info_dict.get("need_all", True)
        self.storages = info_dict.get("storages", [])
        self.mount_point = info_dict.get("mount_point", "")

        self.to_dict()
        
    def to_database(self):
        """
        将卷信息存储到数据库中。
        """
        # 这里需要实现将卷信息存储到数据库的逻辑
        logging.error("to_database not finished")

    def check_volume(self):
        """
        检查卷的健康状态（全量扫描）。
        """
        # 这里需要实现检查卷健康状态的逻辑
        logging.error("check_volume not finished")

    def monitor_volume(self):
        """
        监控卷的健康状态（增量扫描）。
        """
        # 这里需要实现监控卷健康状态的逻辑
        logging.error("monitor_volume not finished")

    def formate_volume(self):
        # 格式化磁盘
        logging.error("formate_volume not finished")

    def get_volume_usage(self):
        """
        获取卷的使用情况。
        :return: 卷的使用情况。
        """
        # 这里需要实现获取卷使用情况的逻辑
        logging.error("get_volume_usage not finished")

    # 将对象转换为字典
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "capacity": self.capacity,
            "add_time": self.add_time,
            "last_check": self.last_check,
            "healthy": self.healthy,
            "info": self.info,
            "need_all": self.need_all,
            "storages": self.storages,  # 假设子卷是可序列化的
            "mount_point": self.mount_point
        }

    # 将对象转换为 JSON 字符串
    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=4)
    
    def __str__(self):
        return f"Volume(id={self.id}, name={self.name}, capacity={self.capacity}, add_time={self.add_time}, last_check={self.last_check}, healthy={self.healthy}, info={self.info}, need_all={self.need_all}, sub_volumes={self.sub_volumes}, mount_point={self.mount_point})"