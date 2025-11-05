# 本文件未经测试
import time
import logging
from core.storage.tools import storage_check
from core.storage.tools.get_storage import get_storage
from core.conf import conf
import sqlite3


class Storage:
    def __init__(
        self, id, name, kind, add_time, last_check_time, state, capacity, info
    ):
        self.id = id
        self.name = name
        self.kind = kind
        self.add_time = add_time
        self.last_check_time = last_check_time
        self.state = state
        self.capacity = capacity
        self.info = info

        self.device_path = None
        

    @classmethod
    def from_default(cls):
        now = int(time.time())
        return cls(
            id="00000000000000000000000000000000",
            name="default",
            kind="disk",
            add_time=now,
            last_check_time=now,
            state="healthy",
            capacity=0,
            info="用于默认和缺省的类",
        )

    def write_back_to_db(self):
        """
        检查数据库中是否存在对应id，存在则只更新发生变化的字段。
        """
        db_path = conf.get("db_path")
        if not db_path:
            raise ValueError('conf["db_path"] 未设置')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, kind, add_time, last_check_time, state, capacity, info FROM storages WHERE id=?",
            (self.id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"数据库中不存在id={self.id}的storage")
        # 只更新发生变化的字段
        fields = [
            "name",
            "kind",
            "add_time",
            "last_check_time",
            "state",
            "capacity",
            "info",
        ]
        updates = []
        values = []
        for i, field in enumerate(fields, 1):
            if getattr(self, field) != row[i]:
                updates.append(f"{field}=?")
                values.append(getattr(self, field))
        if updates:
            sql = f"UPDATE storages SET {', '.join(updates)} WHERE id=?"
            values.append(self.id)
            cursor.execute(sql, tuple(values))
            conn.commit()
        conn.close()

    # from_db 方法已迁移至 StorageFactory

    def check(self):
        mapped_kind = conf.map_kind_to_type(self.kind)
        if mapped_kind == "hdd":
            storage_check.hdd_check(self)
        elif mapped_kind == "tape":
            storage_check.tape_check(self)
        elif mapped_kind == "ssd":
            storage_check.ssd_check(self)
        else:
            raise ValueError(f"未知的存储类型: {self.kind} (映射后: {mapped_kind})")
        self.last_check_time = int(time.time())
        self.write_back_to_db()

    def set_path(self, path):
        """
        设置设备路径
        """
        self.device_path = path

    def to_json(self):
        """
        返回当前Storage实例的字典表示，便于序列化为JSON
        """
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "add_time": self.add_time,
            "last_check_time": self.last_check_time,
            "state": self.state,
            "capacity": self.capacity,
            "info": self.info,
            "device_path": self.device_path
        }

    def insert_to_db(self):
        """
        将当前Storage实例插入数据库，若序列号已存在则抛出异常
        """
        db_path = conf.get("db_path")
        if not db_path:
            raise ValueError('conf["db_path"] 未设置')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM storages WHERE id=?", (self.id,))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"磁盘序列号 {self.id} 已存在，不能重复注册")
        cursor.execute(
            "INSERT INTO storages (id, name, kind, add_time, last_check_time, state, capacity, info) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                self.id,
                self.name,
                self.kind,
                self.add_time,
                self.last_check_time,
                self.state,
                self.capacity,
                self.info
            )
        )
        conn.commit()
        conn.close()
