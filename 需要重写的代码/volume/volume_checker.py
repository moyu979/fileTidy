from datetime import datetime
import json
import logging
import os
import sqlite3
from pathlib import Path
from conf import conf
from volume.tools.id_generate import generate_id


class checker:
    base_path = Path(__file__).resolve().parent
    json_path = base_path / "volume_item_prompt.json"
    # 载入数据文件
    if not json_path.exists():
        logging.error(f"找不到 JSON 文件：{json_path}")
        raise FileNotFoundError(f"找不到 JSON 文件：{json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    fields: dict = schema.get("fields", {})
    logging.debug("载入域文件成功")

    def __init__(self):
        self.time = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

    def __call__(self, key: str, value) -> bool:
        """
        将输入的值合法化：
        合法：原样返回
        不合法但可使用默认值：使用默认值
        不合法且不可修复：抛出错误信息
        """
        if key == "storages":
            return self.check_storages(value)
        elif key == "mount_point":
            return self.check_mount_point(value)
        elif key == "id":
            return self.check_id(value)
        elif key in ["add_time", "last_check"]:
            return self.check_time(key, value)
        else:
            return self.check_others(key, value)

    def check_storages(self, storages):
        """
        检查是storages否合法，主要是检查是storages中的每一个值是否存在于storage表中，即是否使用了未登记的storage
        """
        to_return = True
        for storage in storages:
            to_return = to_return and self.check_storage(storage)

        if self.fields.get("storages", {}).get("must_legal", False) and not to_return:
            raise ValueError("要求storages必须合法，但是实际上不合法")
        elif to_return:
            return storages
        else:
            return []

    def check_storage(self, storage):
        """
        检查是storage否合法，即是否使用了未登记的storage
        """
        if storage is None:
            return False
        conn = sqlite3.connect(conf.get("db_path"))
        cursor = conn.cursor()
        try:
            datas = cursor.execute(
                "SELECT 1 FORM Storage WHERE id=?", (storage,)
            ).fetchone()
            if datas is not None:
                return True
            else:
                return False
        except sqlite3.Error as e:
            return False
        finally:
            cursor.close()
            conn.close()

    def check_mount_point(self, mount_point):
        if mount_point is None:
            return None
        else:
            if os.path.exists(mount_point):
                data_path = os.path.join(mount_point, "datas")
                info_path = os.path.join(mount_point, "volume_info")

                if os.path.exists(data_path) and os.path.exists(info_path):
                    return mount_point
                else:
                    return None
            return None

    def check_id(self, id):
        id = self.check_others("id", id)
        if id is None:
            logging.error("id is None,自动生成id")
            return generate_id()

    def check_time(self, key, time):
        time = self.check_others(key=key, value=time)
        if time is None:
            logging.error(f"{key} is None,自动生成{key}")
            return self.time

    def check_others(self, key, value):
        if self.fields.get(key, None) is None:
            logging.error(f"Key '{key}' not found in fields.")
            raise ValueError(f"需要的键值{key}不存在")
        else:
            allows = self.fields.get(key, {}).get("allows", None)
            not_allows = self.fields.get(key, {}).get("not_allows", None)

            if not_allows is not None:
                if value in not_allows:
                    logging.info(f"键{key}的值{value}位于不允许出现的值{not_allows}中")
                    if self.fields.get(key, {}).get("must_legal", False):
                        raise ValueError(
                            f"键{key}的值{value}位于不允许出现的值{not_allows}中"
                        )
                    else:
                        return None

            if allows is not None:
                if value not in allows:
                    logging.info(f"键{key}的值{value}不位于必须出现的值{allows}中")
                    if self.fields.get(key, {}).get("must_legal", False):
                        raise ValueError(
                            f"键{key}的值{value}不位于必须出现的值{allows}中"
                        )
                    else:
                        return None

            return value
