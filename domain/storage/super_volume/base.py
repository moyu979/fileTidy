import json
from abc import ABC
from datetime import datetime
from enum import Enum

from domain.storage.super_volume.enum import SuperVolumeState


class SuperVolume(ABC):
    def __init__(self,
        serial: str,
        name: str,
        svtype: str,
        method: str,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperVolumeState,
        info: str,
        volumes: list[str],
    ) -> None:
        self.serial = serial
        self.name = name
        self.svtype = svtype
        self.method = method
        self.add_time = add_time
        self.last_check_time = last_check_time
        self.state = state
        self.info = info
        self.volumes = volumes

    def to_snapshot(self) -> dict:
        return {
            "serial": self.serial,
            "name": self.name,
            "type": self.svtype,
            "method": self.method,
            "add_time": self._ts(self.add_time),
            "last_check_time": self._ts(self.last_check_time),
            "state": self.state,
            "info": self.info,
            "volumes": list(self.volumes),
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
