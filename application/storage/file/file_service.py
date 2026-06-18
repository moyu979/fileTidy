from datetime import datetime
from pathlib import Path

import pandas as pd

from domain.storage.file.events import FileRegistered
from domain.storage.file.repo import file_repository_abc
from domain.storage.file.new_file import NewFile
from infra.operate_log.operate_log import log_event
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
        """file path 要带datas层，volume path也已经带了datas"""
        folder = Path(folder_path).resolve()
        data_root = Path(volume_path).resolve()
        registered: list[NewFile] = []

        for fpath in sorted(folder.rglob("*"), key=lambda p: str(p)):
            if not fpath.is_file():
                continue
            abs_path = fpath.resolve()
            now_path = abs_path.relative_to(data_root).as_posix()

            new_file = NewFile(
                sha512=self._hasher.get_sha512(str(fpath)),
                md5=self._hasher.get_md5(str(fpath)),
                size=get_file_size(str(fpath)),
                add_time=datetime.fromtimestamp(fpath.stat().st_mtime),
                path=str(fpath),
                now_path=now_path,
                now_volume=volume_serial,
            )
            self.file_repo.reg_file(new_file)
            registered.append(new_file)
            log_event(FileRegistered(new_file))
        return registered

    def register_by_csv(
        self,
        df: pd.DataFrame,
        volume_serial: str,
        volume_path: str,
    ) -> list[NewFile]:
        """通过 DataFrame 登记文件记录。

        DataFrame 必须包含列: sha256, hash, size, path
        - sha256: 文件的 SHA-256 哈希（存入 sha512 字段）
        - hash:   文件的 MD5 哈希
        - size:   文件大小（字节）
        - path:   文件的绝对路径
        """
        data_root = Path(volume_path).resolve()
        registered: list[NewFile] = []
        add_time = datetime.now()

        for _, row in df.iterrows():
            abs_path = str(row["path"])
            try:
                now_path = str(Path(abs_path).relative_to(data_root).as_posix())
            except ValueError:
                now_path = str(Path(abs_path).name)

            new_file = NewFile(
                sha512=str(row["sha256"]),
                md5=str(row["hash"]),
                size=int(row["size"]),
                add_time=add_time,
                path=abs_path,
                now_path=now_path,
                now_volume=volume_serial,
            )
            self.file_repo.reg_file(new_file)
            registered.append(new_file)
            log_event(FileRegistered(new_file))

        return registered

    