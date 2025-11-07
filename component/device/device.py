# 本文件未经测试
import time

from sqlalchemy.exc import IntegrityError

class device:
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
        now = str(int(time.time()))
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
    def from_model(cls, model: StorageModel):
        return cls(
            id=model.id,
            name=model.name,
            kind=model.kind,
            add_time=model.add_time,
            last_check_time=model.last_check_time,
            state=model.state,
            capacity=model.capacity,
            info=model.info,
        )

    def write_back_to_db(self):
        """
        检查数据库中是否存在对应id，存在则只更新发生变化的字段。
        """
        with session_scope() as session:
            storage = session.get(StorageModel, self.id)
            if storage is None:
                raise ValueError(f"数据库中不存在id={self.id}的storage")

            fields = [
                "name",
                "kind",
                "add_time",
                "last_check_time",
                "state",
                "capacity",
                "info",
            ]
            for field in fields:
                new_value = getattr(self, field)
                if getattr(storage, field) != new_value:
                    setattr(storage, field, new_value)
    def check(self):
        mapped_kind = map_kind_to_type(self.kind)
        if mapped_kind == "hdd":
            storage_check.hdd_check(self)
        elif mapped_kind == "tape":
            storage_check.tape_check(self)
        elif mapped_kind == "ssd":
            storage_check.ssd_check(self)
        else:
            raise ValueError(f"未知的存储类型: {self.kind} (映射后: {mapped_kind})")
        self.last_check_time = str(int(time.time()))
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
        with session_scope() as session:
            if session.get(StorageModel, self.id):
                raise ValueError(f"磁盘序列号 {self.id} 已存在，不能重复注册")
            storage = StorageModel(
                id=self.id,
                name=self.name,
                kind=self.kind,
                add_time=str(self.add_time),
                last_check_time=str(self.last_check_time),
                state=self.state,
                capacity=self.capacity,
                info=self.info,
            )
            session.add(storage)
            try:
                session.flush()
            except IntegrityError as exc:
                raise ValueError(f"插入存储设备失败：{exc}") from exc
    