"""
设备层抽象，用于管理硬件设备，主要用于提供操作硬件设备的抽象,包括：
- 硬盘
- 磁带
    - lto5
    - lto6
- TF卡
- 其他硬件设备

主要用于提供操作硬件设备的抽象
本文件是一个抽象层，具体的实现中drivers里 
"""
import json
from abc import ABC
from enum import Enum

from infra.persistence.database import session_scope



class Device(ABC):
    def __init__(self, 
    serial: str,
    name: str,
    dtype: str|None,
    add_time,
    last_check_time,
    capacity: int|None,
    info: str|None,
    state: str|None=None,
    device_path: str|None=None,
    ) -> None:
        self.serial = serial  # 设备的序列号
        self.name = name  # 设备的名称
        self.dtype = dtype  # 设备的类型
        self.add_time = add_time  # 设备的添加时间
        self.last_check_time = last_check_time  # 设备的最后一次检查时间
        self.state = state  # 设备的状态
        self.capacity = capacity  # 设备的容量
        self.info = info  # 设备的其他信息
        self.device_path = device_path  # 设备的实际挂载路径，如果是None，说明这个设备没挂载
        

    def to_snapshot(self) -> dict:
        return {
            "serial": self.serial,
            "name": self.name,
            "type": self.dtype,
            "add_time": self._ts(self.add_time),
            "last_check_time": self._ts(self.last_check_time),
            "capacity": self.capacity,
            "info": self.info,
            "state": self.state,
            "device_path": self.device_path,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_snapshot(),
            ensure_ascii=False,
            default=self._json_default,
        )

    def __str__(self) -> str:
        return self.to_json()

    def _json_default(self, o: object) -> object:
        if isinstance(o, Enum):
            return o.value
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


    def _ts(self, t):
        if t is None:
            return None
        if hasattr(t, "isoformat"):
            return t.isoformat()
        return t
