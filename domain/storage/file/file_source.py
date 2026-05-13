import json
from enum import Enum
from pathlib import Path


class file_source:
    def __init__(
        self,
        sha512,
        md5,
        size,
        add_time,
        from_path,
        state,
        info,
    ) -> None:
        self.sha512 = sha512
        self.md5 = md5
        self.size = size
        self.add_time = add_time
        self.from_path = from_path
        self.state = state
        self.info = info

    def to_snapshot(self) -> dict:
        from_path = self.from_path
        if isinstance(from_path, Path):
            from_path = from_path.as_posix()
        return {
            "sha512": self.sha512,
            "md5": self.md5,
            "size": self.size,
            "add_time": self._ts(self.add_time),
            "from_path": from_path,
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
