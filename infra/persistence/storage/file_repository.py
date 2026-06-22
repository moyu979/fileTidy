from pathlib import Path

from domain.storage.file.repo import file_repository_abc
from domain.storage.file.new_file import NewFile
from infra.persistence.database import session_scope
from infra.persistence.models import FileLocationsModel, FileSourcesModel


def _path_as_text(p: str | Path | None) -> str | None:
    if p is None:
        return None
    if isinstance(p, Path):
        return p.as_posix()
    return p


class file_repository(file_repository_abc):
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory
        super().__init__()

    def is_exist(self) -> bool:
        pass

    def reg_file(self, new_file: NewFile) -> None:
        # TODO: 重复登记同一文件时：
        #   1. session.add(source_row) → FileSourcesModel 无唯一约束，
        #      会产生冗余记录。
        #   2. session.merge(location_row) → FileLocationsModel 的
        #      (now_volume, now_path) 主键已存在时静默覆盖，无任何通知。
        #   应统一处理重复策略（报错 / 跳过 / 覆盖并记录日志）。
        source_row = FileSourcesModel(
            sha512=new_file.sha512,
            md5=new_file.md5,
            size=new_file.size,
            add_time=new_file.add_time,
            from_path=_path_as_text(new_file.from_path),
            state=new_file.state if new_file.state is not None else "online",
            info=new_file.info if new_file.info is not None else "",
        )
        location_row = FileLocationsModel(
            sha512=new_file.sha512,
            md5=new_file.md5,
            size=new_file.size,
            add_time=new_file.add_time,
            now_path=_path_as_text(new_file.now_path) or "",
            now_volume=new_file.now_volume,
            state=new_file.state if new_file.state is not None else "online",
            info=new_file.info if new_file.info is not None else "",
        )
        with session_scope(self.session_factory) as session:
            session.add(source_row)
            session.merge(location_row)


