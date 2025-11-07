# 本文件未经测试
import json
import time
import logging

from core.database.init import session_scope
from core.database.models import StorageModel
from core.storage.storage import Storage
from core.storage.tools.get_storage import get_storage
from core.storage.tools.detect_device_type import get_device_type

logger = logging.getLogger(__name__)

all_storages = []  # 全局存储所有 Storage 实例

class StorageFactory:
    @staticmethod
    def from_db(id):
        """
        从数据库加载指定 id 的 Storage 实例。
        :param id: storage 的唯一标识
        :return: Storage 实例或 None
        """
        with session_scope() as session:
            model = session.get(StorageModel, id)
            if model is None:
                return None
            return Storage.from_model(model)

    @staticmethod
    def init_storage():
        """
        初始化所有存储设备实例，并根据磁盘信息设置device_path
        """
        global all_storages
        all_storages.clear()
        with session_scope() as session:
            storage_entities = [
                Storage.from_model(model) for model in session.query(StorageModel).all()
            ]

        # 获取所有磁盘信息
        disk_list = get_storage() or []
        # 构建id到磁盘路径的映射
        disk_id_path_map = {str(disk.get("id")): disk.get("path") for disk in disk_list}
        # 创建Storage实例并设置device_path
        for storage in storage_entities:
            disk_path = disk_id_path_map.get(str(storage.id))
            if disk_path:
                storage.set_path(disk_path)
            all_storages.append(storage)
        logger.info(f"初始化存储设备完成，共初始化 {len(all_storages)} 个存储设备")

    @staticmethod
    def to_json():
        """
        将所有Storage实例转为JSON字符串
        """
        global all_storages
        return json.dumps(
            [s.to_json() for s in all_storages], ensure_ascii=False, indent=4
        )

    @staticmethod
    def exists(id):
        """
        判断指定id的Storage是否存在于缓存（all_storages）中
        """
        global all_storages
        return any(str(s.id) == str(id) for s in all_storages)
    
    @staticmethod
    def exists_path(path):
        """
        判断指定id的Storage是否存在于缓存（all_storages）中
        """
        global all_storages
        return any(str(s.device_path) == str(path) for s in all_storages)

    @staticmethod
    def get_path(id):
        """
        根据id返回对应Storage的device_path
        """
        global all_storages
        for s in all_storages:
            if str(s.id) == str(id):
                return s.device_path
        return None

    @staticmethod
    def register(path):
        """
        注册新设备：
        - 若为磁盘：保持原有注册逻辑
        - 若为磁带：留空（不进行注册）
        """
        device_type = get_device_type(path)
        if device_type == "tape":
            # 磁带：留空，不做任何注册动作
            return None
        elif device_type == "disk":
            disk_list = get_storage() or []
            disk_info = next((d for d in disk_list if str(d.get("path")) == str(path)), None)
            if not disk_info:
                raise ValueError(f"未找到路径为 {path} 的磁盘")
            disk_id = str(disk_info.get("id"))
            now = str(int(time.time()))
            storage = Storage(
                id=disk_id,
                name=f"disk_{disk_id}",
                kind="disk",
                add_time=now,
                last_check_time=now,
                state="healthy",
                capacity=disk_info.get("size", 0),
                info="自动注册"
            )
            storage.set_path(path)
            try:
                storage.insert_to_db()
            except ValueError as e:
                raise e
            all_storages.append(storage)
            return storage

    @staticmethod
    def get_storage_id_by_path(path):
        """
        根据路径获取storage id
        """
        global all_storages
        for s in all_storages:
            if str(s.device_path) == str(path):
                return s.id
        return None