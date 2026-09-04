# CHECK: 待检查 - 领域层 File 实体 - 文件核心数据模型
# NOTE: file 子系统未完成（设计未定稿），以下为探索/临时实现，勿作为稳定功能依赖；后续可能整体重写或删除。

from pathlib import Path

from domain.common.mixins import JsonSerializableMixin
from domain.storage.file.enum import FileState


class NewFile(JsonSerializableMixin):
    """
    代表一个正在被注册的新文件。

    文件被放入卷时创建，内部同时持有来源视角（绝对路径）和位置视角（卷内相对路径），
    由 repo 在持久化时拆分为 FileSourcesModel 和 FileLocationsModel 两条记录。
    """

    def __init__(
        self,
        sha512: str,
        md5: str,
        size: int,
        add_time,
        path: str | Path,
        now_path: str | Path,
        now_volume: str,
        state: str | FileState = FileState.ONLINE,
        info: str = "",
    ) -> None:
        """初始化新文件实例。

        Args:
            sha512: 文件的 SHA-512 哈希值。
            md5: 文件的 MD5 哈希值。
            size: 文件大小（字节）。
            add_time: 添加时间。
            path: 文件来源路径（绝对路径）。
            now_path: 文件当前所在卷内的相对路径。
            now_volume: 文件当前所在卷的标识。
            state: 文件状态，默认为 ONLINE。
            info: 附加信息。
        """
        self.sha512 = sha512
        self.md5 = md5
        self.size = size
        self.add_time = add_time
        self.state = state
        self.info = info

        # —— 来源视角 ——
        self.from_path = path

        # —— 位置视角 ——
        self.now_path = now_path
        self.now_volume = now_volume

    def to_snapshot(self) -> dict:
        """将新文件转换为快照字典。

        Returns:
            包含文件所有字段的字典，路径会转换为 POSIX 格式，时间会格式化为 ISO 字符串。
        """
        from_path = self.from_path
        if isinstance(from_path, Path):
            from_path = from_path.as_posix()
        now_path = self.now_path
        if isinstance(now_path, Path):
            now_path = now_path.as_posix()
        return {
            "sha512": self.sha512,
            "md5": self.md5,
            "size": self.size,
            "add_time": self._ts(self.add_time),
            "from_path": from_path,
            "now_volume": self.now_volume,
            "now_path": now_path,
            "state": self.state,
            "info": self.info,
        }
