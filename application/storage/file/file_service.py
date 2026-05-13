from datetime import datetime
from pathlib import Path

from domain.storage.file.file_location import file_location
from domain.storage.file.file_repo import file_repository_abc
from domain.storage.file.file_source import file_source
from domain.storage.volume.base import Volume
from infra.system.storage.file.get_file_size import get_file_size
from infra.system.storage.file.hash import get_md5, get_sha512


class file_service:
    def __init__(self,file_repo:file_repository_abc) -> None:
        self.file_repo=file_repo
        pass

    def reg_file_by_path(self, path: str | Path, volume: Volume) -> None:
        self.reg_file_source_by_path(path, volume)

    def reg_file_source_by_path(self, path: str | Path, volume: Volume) -> None:
        abs_path = Path(path).resolve()
        path_str = str(abs_path)
        md5 = get_md5(path_str)
        sha512 = get_sha512(path_str)
        size = get_file_size(path_str)
        add_time = datetime.now()
        from_path = path_str
        state = "online"
        info = ""

        if not volume.volume_path:
            raise ValueError("volume.volume_path 不能为空")
        volume_root = Path(volume.volume_path).resolve()
        # 卷内数据根目录（与 volume 初始化时的 data 目录一致）
        data_root = volume_root / "data"
        now_path: Path = abs_path.relative_to(data_root)
        now_volume = volume.serial

        file_s = file_source(
            sha512=sha512,
            md5=md5,
            size=size,
            add_time=add_time,
            from_path=from_path,
            state=state,
            info=info,
        )
        file_loc = file_location(
            sha512=sha512,
            md5=md5,
            size=size,
            add_time=add_time,
            now_path=now_path,
            now_volume=now_volume,
            state=state,
            info=info,
        )
        self.file_repo.reg_file(file_s, file_loc)

