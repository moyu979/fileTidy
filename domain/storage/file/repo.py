# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 File 仓储接口 - 文件持久化抽象
# NOTE: file 子系统未完成（设计未定稿），以下为探索/临时实现，勿作为稳定功能依赖；后续可能整体重写或删除。

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from domain.storage.file.new_file import NewFile


# TODO(P1): is_exist() 缺少文件参数，待设计确定后补充
class FileRepositoryABC(ABC):
    """文件仓储抽象基类。

    定义文件持久化操作的接口规范，所有具体文件仓储实现需继承此类。
    """
    def __init__(self,) -> None:
        """初始化文件仓储抽象基类。"""
        pass

    @abstractmethod
    def is_exist(self) -> bool:
        """检查文件是否已存在于仓储中。

        Returns:
            True 表示文件已存在，False 表示不存在。
        """
        pass

    @abstractmethod
    def reg_file(self, new_file: NewFile) -> None:
        """注册（新增）文件到仓储。

        Args:
            new_file: 待注册的新文件实例。
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

    
