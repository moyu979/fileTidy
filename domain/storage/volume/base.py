import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

from domain.storage.file.new_file import NewFile
from domain.storage.super_device.base import SuperDevice
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
            "super_device_id": self.device_id,
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

    # ── 卷内文件查询 / 扫描（repo 由调用方传入）──────────────

    @abstractmethod
    def list_files(
        self,
        repo,
        directory: str = "/",
    ) -> list[NewFile]:
        """列出本卷在数据库中记录的文件。

        委托给传入的 repo 实现，避免 Volume 构造时绑定具体 repo。

        Args:
            repo: volume_repository_abc 实现，用于执行数据库查询。
            directory: 卷内相对路径，默认 "/" 表示全部。

        Returns:
            list[NewFile]: 匹配的文件列表。
        """
        ...

    @abstractmethod
    def scan_files(
        self,
        repo,
        directory: str = "/",
    ) -> tuple[list[NewFile], list[NewFile]]:
        """扫描本卷在磁盘上实际存在的文件，交叉比对后返回两组结果。

        委托给传入的 repo 实现。Volume 自身不持有任何 repo 引用。

        Args:
            repo: volume_repository_abc 实现。
            directory: 卷内相对路径，默认 "/" 表示 datas 下全部。

        Returns:
            tuple[list[NewFile], list[NewFile]]:
                (存在于数据库的文件列表, 不存在于数据库的文件列表)
        """
        ...

    @staticmethod
    def _ts(t):
        if t is None:
            return None
        if hasattr(t, "isoformat"):
            return t.isoformat()
        return t
