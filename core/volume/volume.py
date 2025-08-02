import time
import sqlite3
import os
from core.conf import conf
from core.storage.storage import Storage
from core.file import calculate_hash


class Volume:
    def __init__(
        self,
        id,
        name,
        kind,
        add_time,
        last_check_time,
        state,
        capacity,
        info,
        mount_point=None,
    ):
        self.id = id
        self.name = name
        self.kind = kind
        self.add_time = add_time
        self.last_check_time = last_check_time
        self.state = state
        self.capacity = capacity
        self.info = info
        self.mount_point = mount_point
        self.storages = []  # 存放 Storage 实例

    @classmethod
    def from_db(cls, id):
        db_path = conf.get("db_path")
        if not db_path:
            raise ValueError('conf["db_path"] 未设置')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, kind, add_time, last_check_time, state, capacity, info FROM volumes WHERE id=?",
            (id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        # 读取挂载点（假设 info 字段或其他方式存储）
        mount_point = None
        # 读取所有关联的 storage
        cursor.execute("SELECT sub_id FROM volume_structures WHERE super_id=?", (id,))
        storage_ids = [r[0] for r in cursor.fetchall()]
        storages = []
        for sid in storage_ids:
            storage = Storage.from_db(sid)
            if storage:
                storages.append(storage)
        conn.close()
        v = cls(*row, mount_point=mount_point)
        v.storages = storages
        return v

    def write_back_to_db(self):
        db_path = conf.get("db_path")
        if not db_path:
            raise ValueError('conf["db_path"] 未设置')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, kind, add_time, last_check_time, state, capacity, info FROM volumes WHERE id=?",
            (self.id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"数据库中不存在id={self.id}的volume")
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
            sql = f"UPDATE volumes SET {', '.join(updates)} WHERE id=?"
            values.append(self.id)
            cursor.execute(sql, tuple(values))
            conn.commit()
        conn.close()

    def file_check(self):
        """
        遍历挂载点下所有文件，计算md5并与数据库比对，出错则输出。
        数据库的now_path为相对路径，应使用mount_point+相对路径拼接物理路径，查询时用相对路径。
        """
        db_path = conf.get("db_path")
        if not self.mount_point:
            print(f"[FILE CHECK] 卷 {self.id} 未设置挂载点，跳过文件校验")
            return
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for root, dirs, files in os.walk(self.mount_point):
            for fname in files:
                fpath = os.path.join(root, fname)
                # 计算相对路径（相对于mount_point）
                rel_path = os.path.relpath(
                    fpath, os.path.join(self.mount_point, "datas")
                )
                # 计算md5
                try:
                    md5 = calculate_hash.calculate_md5(fpath)
                except Exception as e:
                    print(f"[FILE CHECK ERROR] 计算 {fpath} md5 失败: {e}")
                    continue
                # 查询数据库

                cursor.execute("SELECT md5 FROM files WHERE now_path=?", (rel_path,))
                row = cursor.fetchone()
                if not row:
                    print(f"[FILE CHECK WARNING] 数据库中未找到 {rel_path}")
                elif row[0] != md5:
                    print(
                        f"[FILE CHECK ERROR] {rel_path} md5 不一致，实际: {md5}，数据库: {row[0]}"
                    )
        conn.close()

    def storage_check(self):
        for storage in self.storages:
            storage.check()

    def check(self, do_storage_check=True, do_file_check=False):
        if do_storage_check:
            self.storage_check()
        if do_file_check:
            self.file_check()
        self.last_check_time = int(time.time())
        self.write_back_to_db()
