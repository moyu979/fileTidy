import time
from core.storage.tools import storage_check
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

    @classmethod
    def from_db(cls, id):
        """
        从数据库加载指定 id 的 storage 实例。
        :param id: storage 的唯一标识
        :return: Storage 实例或 None
        """

        db_path = conf.get("db_path")
        if not db_path:
            raise ValueError('conf["db_path"] 未设置')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, kind, add_time, last_check_time, state, capacity, info FROM storages WHERE id=?",
            (id,),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return cls(*row)
        else:
            return None

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
