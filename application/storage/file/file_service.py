from datetime import datetime
from pathlib import Path

from domain.storage.file.file_repo import file_repository_abc
from domain.storage.file.new_file import NewFile
from infra.system.storage.file.get_file_size import get_file_size
from infra.system.storage.file.hash import file_hash


class file_service:
    def __init__(self, file_repo: file_repository_abc, hasher: file_hash) -> None:
        self.file_repo = file_repo
        self._hasher = hasher

    def register_folder(
        self,
        folder_path: str,
        volume_serial: str,
        volume_path: str,
    ) -> list[NewFile]:
        """遍历文件夹下所有文件，生成 NewFile 并登记。"""
        folder = Path(folder_path).resolve()
        registered: list[NewFile] = []

        for fpath in sorted(folder.rglob("*"), key=lambda p: str(p)):
            if not fpath.is_file():
                continue
            new_file = NewFile(
                sha512=self._hasher.get_sha512(str(fpath)),
                md5=self._hasher.get_md5(str(fpath)),
                size=get_file_size(str(fpath)),
                add_time=datetime.fromtimestamp(fpath.stat().st_mtime),
                path=str(fpath),
                volume_serial=volume_serial,
                volume_path=volume_path,
            )
            self.file_repo.reg_file(new_file)
            registered.append(new_file)

        return registered

    