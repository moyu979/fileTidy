from abc import ABC
from domain.storage.device.base import Device as DeviceBase

class Volume(ABC):
    def __init__(self,
        id: str,
        name: str,
        type: str,
        method: str,

        add_time,
        last_check_time,
        state: str|None,

        capacity: int|None,
        unique_mount_point: str|None,
        info: str|None,
        
        volume_path: str|None,
        based_on: list[DeviceBase]|None,
    ) -> None:

        self.id = id
        self.name = name
        self.type = type
        self.method = method
        self.add_time = add_time
        self.last_check_time = last_check_time
        self.state = state
        self.capacity = capacity
        self.unique_mount_point = unique_mount_point
        self.info = info
        # 现在的挂载点
        self.volume_path = volume_path
        # 基于哪些device构成
        self.based_on = based_on

    def to_snapshot(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "method": self.method,
            "add_time": self._ts(self.add_time),
            "last_check_time": self._ts(self.last_check_time),
            "state": self.state,
            "capacity": self.capacity,
            "unique_mount_point": self.unique_mount_point,
            "info": self.info,
            "volume_path": self.volume_path,
            "based_on": self.based_on,
        }

    def _ts(self, t):
        if t is None:
            return None
        if hasattr(t, "isoformat"):
            return t.isoformat()
        return t
