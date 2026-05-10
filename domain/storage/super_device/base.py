import json
from abc import ABC
from datetime import datetime
from enum import Enum

from domain.storage.device.base import Device
from infra.persistence.models import SuperDeviceState


class SuperDevice(ABC):
    def __init__(self,
        serial: str,
        name: str,
        type: str,
        need_all_devices_online: bool,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperDeviceState,
        capacity: int,
        info: str,
        devices: list[Device],
    ) -> None:
        self.serial = serial
        self.name = name
        self.type = type
        self.need_all_devices_online = need_all_devices_online
        self.add_time = add_time
        self.last_check_time = last_check_time
        self.state = state
        self.capacity = capacity
        self.info = info
        self.devices = devices

    def to_snapshot(self) -> dict:
        return {
            "serial": self.serial,
            "name": self.name,
            "type": self.type,
            "need_all_devices_online": self.need_all_devices_online,
            "add_time": self._ts(self.add_time),
            "last_check_time": self._ts(self.last_check_time),
            "state": self.state,
            "capacity": self.capacity,
            "info": self.info,
            "devices": [d.to_snapshot() for d in self.devices],
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
