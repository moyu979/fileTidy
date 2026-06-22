import json
from abc import ABC
from datetime import datetime
from enum import Enum

from domain.storage.volume.enum import VolumeState


class Volume(ABC):
    def __init__(
        self,
        serial: str,
        device_id: str,
        name: str,
        add_time: datetime,
        last_check_time: datetime,
        state: str | VolumeState,
        capacity: int | None,
        unique_mount_point: str | None,
        file_system: str,
        info: str | None,
        volume_path: str | None,
    ) -> None:
        self.serial = serial
        self.device_id = device_id
        self.name = name
        self.add_time = add_time
        self.last_check_time = last_check_time
        self.state = state
        self.capacity = capacity
        self.unique_mount_point = unique_mount_point
        self.file_system = file_system
        self.info = info
        self.volume_path = volume_path

    def to_snapshot(self) -> dict:
        return {
            "serial": self.serial,
            "device_id": self.device_id,
            "name": self.name,
            "add_time": self._ts(self.add_time),
            "last_check_time": self._ts(self.last_check_time),
            "state": self.state,
            "capacity": self.capacity,
            "unique_mount_point": self.unique_mount_point,
            "file_system": self.file_system,
            "info": self.info,
            "volume_path": self.volume_path,
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

    @staticmethod
    def _ts(t):
        if t is None:
            return None
        if hasattr(t, "isoformat"):
            return t.isoformat()
        return t
