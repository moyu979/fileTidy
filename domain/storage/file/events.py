# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 File 领域事件 - 文件相关事件定义
# NOTE: file 子系统未完成（设计未定稿），以下为探索/临时实现，勿作为稳定功能依赖；后续可能整体重写或删除。

from domain.storage.file.new_file import NewFile


class FileRegistered:
    """文件注册事件。

    当新文件注册到系统时触发。
    """
    def __init__(self, new_file: NewFile):
        """
        Args:
            new_file: 被注册的新文件实例，其快照将被保存到事件中。
        """
        self.file = new_file.to_snapshot()


class FileMoved:
    """文件被移动事件：源文件转移到新的目标位置。"""

    def __init__(
        self,
        sha512: str,
        md5: str,
        source_volume: str,
        source_path: str,
        target_volume: str,
        target_path: str,
    ):
        """
        Args:
            sha512: 文件的 SHA-512 哈希值。
            md5: 文件的 MD5 哈希值。
            source_volume: 源卷标识。
            source_path: 源路径。
            target_volume: 目标卷标识。
            target_path: 目标路径。
        """
        self.sha512 = sha512
        self.md5 = md5
        self.source_volume = source_volume
        self.source_path = source_path
        self.target_volume = target_volume
        self.target_path = target_path


class FileCopied:
    """文件被复制事件：源文件内容复制到目标位置。"""

    def __init__(
        self,
        sha512: str,
        md5: str,
        source_volume: str,
        source_path: str,
        target_volume: str,
        target_path: str,
    ):
        """
        Args:
            sha512: 文件的 SHA-512 哈希值。
            md5: 文件的 MD5 哈希值。
            source_volume: 源卷标识。
            source_path: 源路径。
            target_volume: 目标卷标识。
            target_path: 目标路径。
        """
        self.sha512 = sha512
        self.md5 = md5
        self.source_volume = source_volume
        self.source_path = source_path
        self.target_volume = target_volume
        self.target_path = target_path
