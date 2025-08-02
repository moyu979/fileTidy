import sqlite3
import logging
import json
import core.conf.conf as conf


class Storage:
    def __init__(self, info_dict=None):
        self.value = {
            "id": None,
            "name": None,
            "kind": None,
            "add_time": None,
            "last_check": None,
            "healthy": None,
            "capacity": None,
            "info": None,
            "path": None,
            "in_db": False,
        }
        # 可以从数据库导出的文件中直接加载
        if info_dict is not None:
            self.set_value("id", info_dict["id"])
            self.set_value("name", info_dict["name"])
            self.set_value("kind", info_dict["kind"])
            self.set_value("add_time", info_dict["add_time"])
            self.set_value("last_check", info_dict["last_check"])
            self.set_value("healthy", info_dict["healthy"])
            self.set_value("info", info_dict["info"])

    def to_dict(self):
        return self.value

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)

    def __str__(self):
        return self.to_json()

    def set_value(self, k, v, check=True):
        if check:
            logging.error("对storage的检查还没写")

        self.value[k] = v
        self.flush()

    def get_value(self, k):
        return self.value[k]

    def to_db(self):
        """
        将一个不存在于数据库中的硬件写入数据库
        """
        if self.get_value("in_db"):
            logging.warning(
                f"数据库{self.get_value("id")},{self.get_value("name")}已经在库中，什么都不会做"
            )
        else:
            print("123")
            conn = sqlite3.connect(conf.get("db_path"))
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO storages \
                        (id,name,kind,add_time,last_check,healthy,capacity,info)\
                           VALUES (?,?,?,?,?,?,?,?)",
                (
                    self.get_value("id"),
                    self.get_value("name"),
                    self.get_value("kind"),
                    self.get_value("add_time"),
                    self.get_value("last_check"),
                    self.get_value("healthy"),
                    self.get_value("capacity"),
                    self.get_value("info"),
                ),
            )
            conn.commit()
            conn.close()
        self.set_value("in_db", True)

    def flush(self):
        """
        将所有理论上应该存在于数据库的东西刷回去
        """

        if self.get_value("in_db"):
            connect = sqlite3.connect(conf.get("db_path"))
            cursor = connect.cursor()
            cursor.execute(
                """
                INSERT INTO your_table (
                    id, name, kind, add_time, last_check, healthy, capacity, info
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    kind = excluded.kind,
                    add_time = excluded.add_time,
                    last_check = excluded.last_check,
                    healthy = excluded.healthy,
                    capacity = excluded.capacity,
                    info = excluded.info
                WHERE
                    name != excluded.name OR
                    kind != excluded.kind OR
                    add_time != excluded.add_time OR
                    last_check != excluded.last_check OR
                    healthy != excluded.healthy OR
                    capacity != excluded.capacity OR
                    info != excluded.info;

                """
            )
            connect.commit()
            connect.close()
        else:
            logging.info("跳过不存在于数据库的存储器")
