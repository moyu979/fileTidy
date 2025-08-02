import json
from pathlib import Path
import volume_manager.volume_checker as checker
from volume_manager.volume import Volume
from init_setting import conf
import sqlite3


class volume_creater:
    """
    用来新建volume的类
    """

    def __init__(self):
        self.values = {}
        self.checker = checker.checker()

    def __call__(self, dict: dict):
        self.check(dict)
        self.insert_to()
        return self.get_volume()

    def check(self, dict: dict):
        for k, v in dict.items():
            self.values[k] = self.checker(k, v)

    def insert_to(self):
        conn = sqlite3.connect(conf.get("db_path"))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Volume (id, name, capacity, used, add_time, last_check, healthy, info, kind)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.values["id"],
                self.values["name"],
                self.values["capacity"],
                self.values["used"],
                self.values["add_time"],
                self.values["last_check"],
                self.values["healthy"],
                self.values["info"],
                self.values["kind"],
            ),
        )

        for storage in self.values["storages"]:
            cursor.execute(
                """
                INSERT INTO storageStructure (superid, subid, addTime, info)
                VALUES (?, ?, ?, ?)
            """,
                (self.values["id"], storage, self.checker.time, ""),
            )

        conn.commit()
        cursor.close()
        conn.close()

    def get_volume(self):
        return Volume(self.values[id])
