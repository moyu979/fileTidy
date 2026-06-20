from abc import ABC, abstractmethod

from domain.storage.file.new_file import NewFile
from domain.storage.volume.base import Volume


class volume_repository_abc(ABC):
    def __init__(self) -> None:
        pass

    def is_exist(self, volume: Volume) -> bool:
        pass

    def reg_volume(self, volume: Volume) -> None:
        pass

    def get_volume(self, volume_id: str) -> Volume:
        pass

    def list_volume(self) -> list[Volume]:
        pass

    # ── 卷内文件查询 / 扫描 ─────────────────────────────────

    @abstractmethod
    def list_files(
        self,
        volume_id: str,
        directory: str = "/",
    ) -> list[NewFile]:
        """列出数据库中记录在指定卷下指定目录的文件。

        以 now_volume == volume_id 且 now_path 以 directory 为前缀
        作为过滤条件，查询文件位置表。

        Args:
            volume_id: 卷序列号。
            directory: 卷内相对路径，默认为 "/" 表示全部。
                       例如传入 "videos/2024" 则只返回该目录下的文件。

        Returns:
            list[NewFile]: 匹配的文件列表；无匹配时返回空列表。
        """
        ...

    @abstractmethod
    def scan_files(
        self,
        volume_id: str,
        volume_path: str,
        directory: str = "/",
    ) -> tuple[list[NewFile], list[NewFile]]:
        """扫描卷上实际存在的文件（走文件系统），与数据库记录交叉比对后返回。

        遍历 volume_path/datas/<directory> 下所有实际文件，
        计算哈希和大小，与数据库中的编目记录比对，区分出「已登记」和「未登记」两类。

        与 list_files 的区别：
            list_files — 仅查数据库（编目记录）
            scan_files — 扫磁盘后交叉比对（实际存在 vs 数据库记录）

        Args:
            volume_id: 卷序列号。
            volume_path: 卷的实际挂载路径（基路径，不含 datas）。
            directory: 卷内相对路径，默认 "/" 表示 datas 下全部。

        Returns:
            tuple[list[NewFile], list[NewFile]]:
                (存在于数据库的文件列表, 不存在于数据库的文件列表)
        """
        ...
