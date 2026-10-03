# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 File 仓储接口 - 文件持久化抽象
# NOTE: file 子系统未完成（设计未定稿），以下为探索/临时实现，勿作为稳定功能依赖；后续可能整体重写或删除。

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Any

from domain.storage.file.new_file import NewFile


class FileRepositoryABC(ABC):
    """文件仓储抽象基类。

    定义文件持久化操作的接口规范，所有具体文件仓储实现需继承此类。
    """
    def __init__(self,) -> None:
        """初始化文件仓储抽象基类。"""
        pass

    @abstractmethod
    def is_exist(self, sha512: str, md5: str) -> bool:
        """检查同时匹配 sha512 与 md5 的文件记录是否已存在于仓储中。

        Args:
            sha512: 文件的 SHA-512 值。
            md5: 文件的 MD5 值。

        Returns:
            True 表示两个哈希同时命中的文件记录已存在，False 表示不存在。
        """
        pass

    @abstractmethod
    def reg_source(self, new_file: NewFile, session: Any = None) -> None:
        """登记文件来源（文件身份/内容）。

        以 sha512 标识文件内容，回答「这个文件是什么、从哪来」。
        一份内容一条来源，与位置记录是一对多关系。
        同一来源（from_path + sha512 + md5 全部相同）重复登记时跳过写入。

        Args:
            new_file: 待登记的文件实例。
            session: 可选的外部事务会话；非空时复用该事务且不自行提交，
                用于与 reg_location 组合成同一事务。
        """
        pass

    @abstractmethod
    def reg_location(self, new_file: NewFile, session: Any = None) -> None:
        """登记文件位置（物理落位）。

        以 (now_volume, now_path) 标识物理位置，回答「这个文件现在在哪」。
        move / copy 只影响位置，不新增来源。

        Args:
            new_file: 待登记的文件实例。
            session: 可选的外部事务会话；非空时复用该事务且不自行提交，
                用于与 reg_source 组合成同一事务。
        """
        pass

    @abstractmethod
    def transaction(self) -> AbstractContextManager[Any]:
        """返回事务上下文，用于把多个写操作组合成同一事务。

        用法::

            with repo.transaction() as session:
                repo.reg_source(new_file, session)
                repo.reg_location(new_file, session)

        Returns:
            可进入的上下文管理器；yield 出的会话需传给各写方法。
        """
        pass

    @abstractmethod
    def list_by_volume_dir(
        self, volume: str, dir_path: str,
    ) -> list[dict[str, Any]]:
        """查询指定卷下，路径以 dir_path/ 开头的所有文件记录。

        Args:
            volume: 卷标识。
            dir_path: 目录路径，匹配该路径前缀的所有文件。

        Returns:
            文件记录字典列表。
        """
        pass

    @abstractmethod
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
        """移动文件记录。

        删除源位置 (src_volume, src_path) 的记录，
        在目标位置 (dst_volume, dst_path) 插入新记录。

        Args:
            sha512: 文件的 SHA-512 哈希值。
            md5: 文件的 MD5 哈希值。
            src_volume: 源卷标识。
            src_path: 源路径。
            dst_volume: 目标卷标识。
            dst_path: 目标路径。
            add_time: 移动时间，为 None 时使用当前时间。
        """
        raise NotImplementedError

    @abstractmethod
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
        """复制文件记录。

        在目标位置 (dst_volume, dst_path) 新增一条记录，
        源记录不受影响。

        Args:
            sha512: 文件的 SHA-512 哈希值。
            md5: 文件的 MD5 哈希值。
            src_volume: 源卷标识。
            src_path: 源路径。
            dst_volume: 目标卷标识。
            dst_path: 目标路径。
            add_time: 复制时间，为 None 时使用当前时间。
        """
        raise NotImplementedError

    
