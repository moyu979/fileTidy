# CHECK: 待检查 - 领域层 Volume 仓储接口 - 卷持久化抽象

from abc import ABC, abstractmethod

from domain.storage.volume.base import Volume


class volume_repository_abc(ABC):
    """卷仓储抽象基类。

    定义卷持久化操作的接口规范，所有具体卷仓储实现需继承此类。
    """
    def __init__(self) -> None:
        """初始化卷仓储抽象基类。"""
        pass

    @abstractmethod
    def is_exist(self, volume: Volume | str) -> bool:
        """检查卷是否已存在于仓储中。

        Args:
            volume: 待检查的卷实例或卷序列号。

        Returns:
            True 表示卷已存在，False 表示不存在。
        """
        pass

    @abstractmethod
    def reg_volume(self, volume: Volume) -> None:
        """注册（新增）卷到仓储。

        Args:
            volume: 待注册的卷实例。
        """
        pass

    @abstractmethod
    def get_volume(self, serial: str) -> Volume | None:
        """根据卷 ID 加载卷。

        Args:
            serial: 卷的序列号。

        Returns:
            对应的 Volume 实例，不存在时返回 None。
        """
        pass

    @abstractmethod
    def list_volumes(self) -> list[Volume]:
        """列出仓储中所有卷。

        Returns:
            卷实例列表。
        """
        pass

    @abstractmethod
    def update_volume(self, serial: str, **fields) -> None:
        """更新卷指定字段。

        Args:
            serial: 要更新的卷序列号。
            **fields: 字段名到新值的映射。
        """
        pass

    @abstractmethod
    def update_serial(self, old_serial: str, new_serial: str) -> None:
        """重置卷序列号，同步更新关联表中的外键引用。

        Args:
            old_serial: 原卷序列号。
            new_serial: 新卷序列号。
        """
        pass

    @abstractmethod
    def remove_volume(self, serial: str) -> None:
        """将卷标记为 REMOVED（软删除），保留记录。

        移除前检查卷是否仍被引用：
        - 仍有未移除的文件位于该卷上（file_locations now_volume state != REMOVED）
        - 仍作为超级卷的子卷（super_volume_structures state=USING）
        存在任意引用则抛出 VolumeInUseError，不执行移除。

        Args:
            serial: 卷序列号。

        Raises:
            VolumeInUseError: 卷仍被引用时抛出。
        """
        pass
