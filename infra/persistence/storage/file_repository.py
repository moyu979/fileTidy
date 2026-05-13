from pathlib import Path

from domain.storage.device.base import Device
from domain.storage.file.file_location import file_location
from domain.storage.file.file_repo import file_repository_abc
from domain.storage.file.file_source import file_source
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

    def reg_file(self, source: file_source, file_location: file_location) -> None:
        source_row = FileSourcesModel(
            sha512=source.sha512,
            md5=source.md5,
            size=source.size,
            add_time=source.add_time,
            from_path=_path_as_text(source.from_path),
            state=source.state if source.state is not None else "online",
            info=source.info if source.info is not None else "",
        )
        location_row = FileLocationsModel(
            sha512=file_location.sha512,
            md5=file_location.md5,
            size=file_location.size,
            add_time=file_location.add_time,
            now_path=_path_as_text(file_location.now_path) or "",
            now_volume=file_location.now_volume,
            state=file_location.state if file_location.state is not None else "online",
            info=file_location.info if file_location.info is not None else "",
        )
        with session_scope(self.session_factory) as session:
            session.add(source_row)
            session.merge(location_row)
