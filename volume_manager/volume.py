from datetime import datetime
import json
import logging
import sqlite3
from pathlib import Path

from init_setting import conf
from volume_manager.tools.id_generate import generate_id

class Volume:
    base_path = Path(__file__).resolve().parent
    json_path = base_path / "volume_item_prompt.json"
    if not json_path.exists():
        raise FileNotFoundError(f"找不到 JSON 文件：{json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    fields = schema.get('fields', {})

    def __init__(self):
        
        self.values = {
            key: meta.get("default", None)
            for key, meta in self.fields.items()
        }

        self.storages = []

    @classmethod
    def get_fileds(cls):
        return cls.fields
    @classmethod
    def get_prompt(cls,key):
        return cls.fields.get(key,{"prompt","not such item"}).get("prompt","not has prompt")
    
    def get_value(self,key):
        return self.values.get(key,{})
    
    def set_value(self,key,value):
        if key in self.fields:
            self.values[key] = value
        else:
            raise KeyError(f"Key '{key}' not found in fields.")
        
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

            # 使用 self.values 替代 self.xx
            self.values["id"] = result[0]
            self.values["name"] = result[1]
            self.values["capacity"] = result[2]
            self.values["used"] = result[3]
            self.values["add_time"] = result[4]
            self.values["last_check"] = result[5]
            self.values["healthy"] = result[6]
            self.values["info"] = result[7]
            self.values["kind"] = result[8]

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

    @classmethod
    def validate_value(cls, key:str, value):
        """
        检查给定的键值对是否符合预期的类型和范围。
        :param key: 要检查的键。
        :param value: 要检查的值。
        :return: 如果符合预期，返回 True；否则返回 False。
        """

        logging.error(f"检查storages是否合法还没做")
        to_return=True

        if value is None:
            to_return=False
        else:
            if key not in Volume.fields:
                logging.error(f"Key '{key}' not found in fields.")
                to_return=False
            else:
                allows=Volume.fields.get(key,{}).get("allows",None)
                not_allows=Volume.fields.get(key,{}).get("not_allows",None)

                if not_allows is not None:
                    if value in not_allows:
                        to_return=False
            
                if allows is not None:
                    if value not in allows:
                        to_return=(to_return and False)
                else:
                    to_return=(to_return and True)
            must=Volume.fields.get(key,{}).get("must",None)
            if must and not to_return:
                logging.error(f"Key '{key}' must be set as a league value.")
                raise ValueError(f"Key '{key}' must be set as a league value.")
            
        return to_return
    
    def new_volume(self, info_dict:dict=None):
        """
        根据 info_dict 的键值对设置卷对象的属性。
        :param info_dict: 包含卷对象属性的字典。
        """
        # 定义允许设置的属性
        now_time=datetime.now().strftime("%Y:%m:%d %H:%M:%S")

        self.values["id"] = info_dict.get("id") if Volume.validate_value("id",info_dict.get("id")) else generate_id()
        self.values["name"] = info_dict.get("name") if Volume.validate_value("name",info_dict.get("name")) else self.values["id"]
        self.values["capacity"] = info_dict.get("capacity") if Volume.validate_value("capacity",info_dict.get("capacity")) else 0
        self.values["used"] = info_dict.get("used") if Volume.validate_value("used",info_dict.get("used")) else 0
        self.values["add_time"] = info_dict.get("add_time") if Volume.validate_value("add_time",info_dict.get("add_time")) else now_time
        self.values["last_check"] = info_dict.get("last_check") if Volume.validate_value("last_check",info_dict.get("last_check")) else now_time
        self.values["healthy"] = info_dict.get("healthy") if Volume.validate_value("healthy",info_dict.get("healthy")) else "health"
        self.values["info"] = info_dict.get("info") if Volume.validate_value("info",info_dict.get("info")) else ""
        self.values["kind"] = info_dict.get("kind") if Volume.validate_value("kind",info_dict.get("kind")) else "single_disk"
        
        self.storages = info_dict.get("storages", [])

        self.mount_point = info_dict.get("mount_point", None)

        self.to_database()
        
    def to_database(self):
        """
        将卷信息存储到数据库中。
        """
        conn=sqlite3.connect(conf.get("db_path"))
        cursor = conn.cursor()
        # 使用 INSERT OR REPLACE 实现存在更新，不存在插入
        cursor.execute("""
            INSERT INTO Storage (id, name, capacity, used, addTime, lastCheck, healthy, info, kind)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                capacity=excluded.capacity,
                used=excluded.used,
                addTime=excluded.addTime,
                lastCheck=excluded.lastCheck,
                healthy=excluded.healthy,
                info=excluded.info
                kind=excluded.kind,
                
        """, (
        self.values["id"],
        self.values["name"],
        self.values["capacity"],
        self.values["used"],
        self.values["add_time"],
        self.values["last_check"],
        self.values["healthy"],
        self.values["info"],
        self.values["kind"]
        ))
        conn.commit()
        conn.close()

        for storage in self.storages:
            conn=sqlite3.connect(conf.get("db_path"))
            cursor = conn.cursor()
            # 使用 INSERT OR REPLACE 实现存在更新，不存在插入
            cursor.execute("""
                INSERT INTO Storage (superid, subid, addTime, info)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(subid) DO UPDATE SET
                    superid=excluded.superid,
                    info=excluded.info,
            """, (
            self.values["id"],
            storage,
            datetime.now().strftime("%Y:%m:%d %H:%M:%S"),
            self.values["info"]
            ))
            conn.commit()
            conn.close()

        # 这里需要实现将卷信息存储到数据库的逻辑
        logging.warning("to_database not checked")

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
            "id": self.values["id"],
            "name": self.values["name"],
            "capacity": self.values["capacity"],
            "used": self.values["used"],

            "add_time": self.values["add_time"],
            "last_check": self.values["last_check"],
            "healthy": self.values["healthy"],
            "info": self.values["info"],
            "kind": self.values["kind"],
            "storages": self.storages,  # 假设子卷是可序列化的
            "mount_point": self.values["mount_point"],
        }

    # 将对象转换为 JSON 字符串
    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=4)
    
    def __str__(self):
        return f"Volume(id={self.id}, name={self.name}, capacity={self.capacity}, add_time={self.add_time}, last_check={self.last_check}, healthy={self.healthy}, info={self.info}, need_all={self.need_all}, sub_volumes={self.sub_volumes}, mount_point={self.mount_point})"