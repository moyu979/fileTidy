# CHECK: 待检查 - 应用层 File 服务 - 文件业务用例编排
# NOTE: file 子系统未完成（设计未定稿），以下为探索/临时实现，勿作为稳定功能依赖；后续可能整体重写或删除。

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from domain.storage.file.enum import FileState
from domain.storage.file.events import FileCopied, FileMoved, FileRegistered
from domain.storage.file.repo import file_repository_abc
from domain.storage.file.new_file import NewFile
from infra.operation_log.operation_log import log_event
from infra.system.storage.file.get_file_size import get_file_size
from infra.common.hash import FileHasher

logger = logging.getLogger(__name__)


# REFACTOR(P1): 类名 file_service 应改为 FileService（PascalCase），符合 PEP8 命名规范
#               同时需要更新 application/app.py 和 bootstrap.py 中的所有引用
class file_service:
    def __init__(self, file_repo: file_repository_abc, hasher: FileHasher) -> None:
        self.file_repo = file_repo
        self._hasher = hasher
        logger.info("FileService constructed")

    def register_folder(
        self,
        folder_path: str,
        volume_serial: str,
        volume_path: str,
        add_time: datetime | None = None,
    ) -> list[NewFile]:
        """遍历文件夹下所有文件，生成 NewFile 并登记。

        Args:
            add_time: 文件的登记时间，不传则使用函数调用时的当前时间。
        """
        """file path 要带datas层，volume path也已经带了datas"""
        folder = Path(folder_path).resolve()
        data_root = Path(volume_path).resolve()
        add_time = add_time or datetime.now()
        registered: list[NewFile] = []

        for fpath in sorted(folder.rglob("*"), key=lambda p: str(p)):
            if not fpath.is_file():
                continue
            abs_path = fpath.resolve()
            now_path = abs_path.relative_to(data_root).as_posix()

            hashes = self._hasher.compute_hash(str(fpath))
            new_file = NewFile(
                sha512=hashes["sha512"],
                md5=hashes["md5"],
                size=get_file_size(str(fpath)),
                add_time=add_time,
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
        add_time: datetime | None = None,
    ) -> list[NewFile]:
        """通过 DataFrame 登记文件记录。

        DataFrame 必须包含列: sha256, hash, size, path
        - sha256: 文件的 SHA-256 哈希（存入 sha512 字段）
        - hash:   文件的 MD5 哈希
        - size:   文件大小（字节）
        - path:   文件的绝对路径

        注意：
          目前对 Windows 风格路径（如 F:\\datas\\...）的支持有问题，
          跨平台场景下请勿使用此方法，待后续统一梳理。

        Args:
            add_time: 文件的登记时间，不传则使用当前时间。
        """
        data_root = Path(volume_path).resolve()
        registered: list[NewFile] = []
        add_time = add_time or datetime.now()

        for _, row in df.iterrows():
            
            abs_path = str(row["path"])
            #print(abs_path)
            #print(data_root)
            #exit()
            try:
                now_path = str(Path(abs_path).relative_to(data_root).as_posix())
            except ValueError:
                now_path = str(Path(abs_path).name)

            new_file = NewFile(
                sha512=str(row["sha512"]),
                md5=str(row["hash"]),
                size=int(row["size"]),
                add_time=add_time,
                path=abs_path,
                now_path=now_path,
                now_volume=volume_serial,
                state=FileState.UNKNOWN,
            )
            self.file_repo.reg_file(new_file)
            registered.append(new_file)
            log_event(FileRegistered(new_file))

        return registered

    # ── moveFile ──────────────────────────────────────────────

    def moveFile(
        self,
        src_volume: str,
        src_root: str,
        src_dir: str,
        dst_volume: str,
        dst_root: str,
        dst_dir: str,
        df: pd.DataFrame,
        add_time: datetime | None = None,
    ) -> None:
        """按 CSV 清单将文件从源卷移动到目标卷。

        CSV 必须包含列: sha256, hash, size, path
        - path: 目标卷上的绝对路径
        """
        add_time = add_time or datetime.now()
        src_prefix = src_dir.rstrip("/")
        dst_root_resolved = Path(dst_root).resolve()

        # 1. 提取源侧 DB 记录
        db_records = self.file_repo.list_by_volume_dir(src_volume, src_prefix)
        db_map: dict[str, dict] = {}
        for r in db_records:
            rel = str(Path(r["now_path"]).relative_to(src_prefix).as_posix())
            db_map[rel] = {"sha512": r["sha512"], "md5": r["md5"]}

        # 2. 解析 CSV → 目标侧记录
        csv_map: dict[str, dict] = {}
        for _, row in df.iterrows():
            abs_path = str(row["path"])
            vol_rel = str(Path(abs_path).relative_to(dst_root_resolved).as_posix())
            rel = str(Path(vol_rel).relative_to(dst_dir).as_posix())
            csv_map[rel] = {"sha512": str(row["sha512"]), "md5": str(row["hash"])}

        # 3. 一致性校验
        db_keys = set(db_map)
        csv_keys = set(csv_map)
        if db_keys != csv_keys:
            raise ValueError(
                f"文件清单不一致。"
                f" 数据库中多余: {db_keys - csv_keys}"
                f" CSV 中多余: {csv_keys - db_keys}"
            )
        for rel in db_keys:
            if db_map[rel] != csv_map[rel]:
                d = db_map[rel]
                c = csv_map[rel]
                raise ValueError(
                    f"哈希不匹配: {rel}  "
                    f"DB(sha512={d['sha512']}, md5={d['md5']})  "
                    f"CSV(sha512={c['sha512']}, md5={c['md5']})"
                )

        # 4. 执行移动
        for rel in sorted(db_keys):
            src_path = f"{src_prefix}/{rel}"
            dst_path = f"{dst_dir}/{rel}"
            sha512 = db_map[rel]["sha512"]
            md5 = db_map[rel]["md5"]
            self.file_repo.move_file(
                sha512, md5, src_volume, src_path, dst_volume, dst_path, add_time,
            )
            log_event(FileMoved(
                sha512=sha512, md5=md5,
                source_volume=src_volume, source_path=src_path,
                target_volume=dst_volume, target_path=dst_path,
            ))

    # ── copyFile ──────────────────────────────────────────────

    def copyFile(
        self,
        src_volume: str,
        src_root: str,
        src_dir: str,
        dst_volume: str,
        dst_root: str,
        dst_dir: str,
        df: pd.DataFrame,
        add_time: datetime | None = None,
    ) -> None:
        """按 CSV 清单将文件从源卷复制到目标卷。

        CSV 必须包含列: sha256, hash, size, path
        - path: 目标卷上的绝对路径
        """
        add_time = add_time or datetime.now()
        src_prefix = src_dir.rstrip("/")
        dst_root_resolved = Path(dst_root).resolve()

        # 1. 提取源侧 DB 记录
        db_records = self.file_repo.list_by_volume_dir(src_volume, src_prefix)
        db_map: dict[str, dict] = {}
        for r in db_records:
            rel = str(Path(r["now_path"]).relative_to(src_prefix).as_posix())
            db_map[rel] = {"sha512": r["sha512"], "md5": r["md5"]}

        # 2. 解析 CSV → 目标侧记录
        csv_map: dict[str, dict] = {}
        for _, row in df.iterrows():
            abs_path = str(row["path"])
            vol_rel = str(Path(abs_path).relative_to(dst_root_resolved).as_posix())
            rel = str(Path(vol_rel).relative_to(dst_dir).as_posix())
            csv_map[rel] = {"sha512": str(row["sha512"]), "md5": str(row["hash"])}

        # 3. 一致性校验
        db_keys = set(db_map)
        csv_keys = set(csv_map)
        if db_keys != csv_keys:
            raise ValueError(
                f"文件清单不一致。"
                f" 数据库中多余: {db_keys - csv_keys}"
                f" CSV 中多余: {csv_keys - db_keys}"
            )
        for rel in db_keys:
            if db_map[rel] != csv_map[rel]:
                d = db_map[rel]
                c = csv_map[rel]
                raise ValueError(
                    f"哈希不匹配: {rel}  "
                    f"DB(sha512={d['sha512']}, md5={d['md5']})  "
                    f"CSV(sha512={c['sha512']}, md5={c['md5']})"
                )

        # 4. 执行复制
        for rel in sorted(db_keys):
            src_path = f"{src_prefix}/{rel}"
            dst_path = f"{dst_dir}/{rel}"
            sha512 = db_map[rel]["sha512"]
            md5 = db_map[rel]["md5"]
            self.file_repo.copy_file(
                sha512, md5, src_volume, src_path, dst_volume, dst_path, add_time,
            )
            log_event(FileCopied(
                sha512=sha512, md5=md5,
                source_volume=src_volume, source_path=src_path,
                target_volume=dst_volume, target_path=dst_path,
            ))

    
