# CHECK: 待检查 - 基础设施 File 仓储实现 - 文件数据持久化
# NOTE: file 子系统未完成（设计未定稿），以下为探索/临时实现，勿作为稳定功能依赖；后续可能整体重写或删除。

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.exc import NoResultFound
from sqlalchemy import func

from domain.storage.file.enum import FileState
from domain.storage.file.repo import file_repository_abc
from domain.storage.file.new_file import NewFile
from infra.persistence.database import session_scope
from infra.persistence.models import FileLocationsModel, FileSourcesModel

logger = logging.getLogger(__name__)


def _path_as_text(p: str | Path | None) -> str | None:
    """
    将路径转换为字符串表示，None 输入返回 None，Path 对象转换为 POSIX 风格。

    Args:
        p: 路径字符串、Path 对象或 None

    Returns:
        POSIX 风格的路径字符串，或 None
    """
    if p is None:
        return None
    if isinstance(p, Path):
        return p.as_posix()
    return p

# REFACTOR(P1): 类名 file_repository 应改为 FileRepository（PascalCase），符合 PEP8 命名规范
class file_repository(file_repository_abc):
    """文件仓库实现，提供文件信息的持久化存储和查询操作。"""

    def __init__(self, session_factory) -> None:
        """
        初始化 file_repository。

        Args:
            session_factory: 用于创建 SQLAlchemy 会话的工厂
        """
        self.session_factory = session_factory
        super().__init__()
        logger.info("FileRepository constructed")

    def is_exist(self) -> bool:
        """判断文件记录是否存在（暂未实现）。"""
        pass

    def reg_file(self, new_file: NewFile) -> None:
        """
        注册一个新文件记录，包含文件源信息和位置信息。

        Args:
            new_file: 要注册的文件对象

        Note:
            当前实现存在重复登记问题，详见 TODO 注释。
        """
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
            state=new_file.state if new_file.state is not None else FileState.ONLINE,
            info=new_file.info if new_file.info is not None else "",
        )
        location_row = FileLocationsModel(
            sha512=new_file.sha512,
            md5=new_file.md5,
            size=new_file.size,
            add_time=new_file.add_time,
            now_path=_path_as_text(new_file.now_path) or "",
            now_volume=new_file.now_volume,
            state=new_file.state if new_file.state is not None else FileState.ONLINE,
            info=new_file.info if new_file.info is not None else "",
        )
        with session_scope(self.session_factory) as session:
            session.add(source_row)
            session.merge(location_row)

    def list_by_volume_dir(
        self, volume: str, dir_path: str,
    ) -> list[dict[str, Any]]:
        """
        列出指定卷下指定目录中的所有文件。

        Args:
            volume: 卷标识
            dir_path: 目录路径

        Returns:
            文件信息字典列表
        """
        prefix = f"{dir_path.rstrip('/')}/"
        with session_scope(self.session_factory) as session:
            rows = session.query(FileLocationsModel).filter(
                FileLocationsModel.now_volume == volume,
                FileLocationsModel.now_path.startswith(prefix),
            ).all()
            return [
                {
                    "sha512": r.sha512,
                    "md5": r.md5,
                    "size": r.size,
                    "now_volume": r.now_volume,
                    "now_path": r.now_path,
                    "state": r.state,
                    "info": r.info,
                    "add_time": r.add_time,
                }
                for r in rows
            ]

    def _make_location_row(
        self,
        sha512: str,
        md5: str,
        size: int,
        now_volume: str,
        now_path: str,
        add_time: datetime | None = None,
        state: FileState = FileState.ONLINE,
        info: str = "",
    ) -> FileLocationsModel:
        """
        创建一个 FileLocationsModel 实例。

        Args:
            sha512: 文件的 SHA-512 值
            md5: 文件的 MD5 值
            size: 文件大小（字节）
            now_volume: 当前所在卷
            now_path: 当前路径
            add_time: 添加时间，默认当前时间
            state: 文件状态
            info: 其他信息

        Returns:
            FileLocationsModel 实例
        """
        return FileLocationsModel(
            sha512=sha512,
            md5=md5,
            size=size,
            add_time=add_time or datetime.now(),
            now_path=now_path,
            now_volume=now_volume,
            state=state,
            info=info,
        )

    def move_file(
        self,
        sha512: str,
        md5: str,
        src_volume: str,
        src_path: str,
        dst_volume: str,
        dst_path: str,
        add_time: datetime | None = None,
    ) -> None:
        """
        移动文件记录：更新文件位置信息。

        Args:
            sha512: 文件的 SHA-512 值
            md5: 文件的 MD5 值
            src_volume: 源卷
            src_path: 源路径
            dst_volume: 目标卷
            dst_path: 目标路径
            add_time: 更新时间，默认当前时间

        Raises:
            LookupError: 源位置不存在
        """
        add_time = add_time or datetime.now()
        with session_scope(self.session_factory) as session:
            row = session.query(FileLocationsModel).filter_by(
                now_volume=src_volume, now_path=src_path,
            ).one_or_none()
            if row is None:
                raise LookupError(
                    f"源位置不存在: 卷={src_volume}, 路径={src_path}"
                )

            row.now_volume = dst_volume
            row.now_path = dst_path
            row.add_time = add_time

    def copy_file(
        self,
        sha512: str,
        md5: str,
        src_volume: str,
        src_path: str,
        dst_volume: str,
        dst_path: str,
        add_time: datetime | None = None,
    ) -> None:
        """
        复制文件记录：在目标位置创建新的文件位置记录。

        Args:
            sha512: 文件的 SHA-512 值
            md5: 文件的 MD5 值
            src_volume: 源卷
            src_path: 源路径
            dst_volume: 目标卷
            dst_path: 目标路径
            add_time: 添加时间，默认当前时间

        Raises:
            LookupError: 源位置不存在
        """
        add_time = add_time or datetime.now()
        with session_scope(self.session_factory) as session:
            src = session.query(FileLocationsModel).filter_by(
                now_volume=src_volume, now_path=src_path,
            ).one_or_none()
            if src is None:
                raise LookupError(
                    f"源位置不存在: 卷={src_volume}, 路径={src_path}"
                )
            size = src.size
            state = src.state
            info = src.info
            new_row = self._make_location_row(
                sha512, md5, size, dst_volume, dst_path, add_time,
                state=state, info=info,
            )
            session.add(new_row)

