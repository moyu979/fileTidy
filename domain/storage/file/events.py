from domain.storage.file.new_file import NewFile


class FileRegistered:
    def __init__(self, new_file: NewFile):
        self.file = new_file.to_snapshot()


class FileMoved:
    """文件被移动：源文件转移到新的目标位置"""

    def __init__(self, new_file: NewFile, target_volume: str, target_path: str):
        self.file = new_file.to_snapshot()
        self.target_volume = target_volume
        self.target_path = target_path


class FileCopied:
    """文件被复制：源文件内容复制到目标位置"""

    def __init__(self, new_file: NewFile, target_volume: str, target_path: str):
        self.file = new_file.to_snapshot()
        self.target_volume = target_volume
        self.target_path = target_path
