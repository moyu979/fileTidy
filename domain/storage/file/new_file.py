import json
from enum import Enum
from pathlib import Path

from domain.storage.file.enum import FileState


class NewFile:
    """
    代表一个正在被注册的新文件。
    文件被放入卷时创建，内部同时持有来源视角（绝对路径）和位置视角（卷内相对路径），
    由 repo 在持久化时拆分为 FileSourcesModel 和 FileLocationsModel 两条记录。
    """

    def __init__(
        self,
        sha512: str,
        md5: str,
        size: int,
        add_time,
        path: str | Path,
        now_path: str | Path,
        now_volume: str,
        state: str | FileState = FileState.ONLINE,
        info: str = "",
    ) -> None:
        self.sha512 = sha512
        self.md5 = md5
        self.size = size
        self.add_time = add_time
        self.state = state
        self.info = info

        # —— 来源视角 ——
        self.from_path = path

        # —— 位置视角 ——
        self.now_path = now_path
        self.now_volume = now_volume

    def to_snapshot(self) -> dict:
        from_path = self.from_path
        if isinstance(from_path, Path):
            from_path = from_path.as_posix()
        now_path = self.now_path
        if isinstance(now_path, Path):
            now_path = now_path.as_posix()
        return {
            "sha512": self.sha512,
            "md5": self.md5,
            "size": self.size,
            "add_time": self._ts(self.add_time),
            "from_path": from_path,
            "now_volume": self.now_volume,
            "now_path": now_path,
            "state": self.state,
            "info": self.info,
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
