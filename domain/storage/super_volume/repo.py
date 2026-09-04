# CHECK: 待检查 - 领域层 SuperVolume 仓储接口 - 超级卷持久化抽象

from abc import ABC, abstractmethod

from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.structure import SuperVolumeStructure


class super_volume_repository_abc(ABC):
    """超级卷仓储抽象基类。

    定义超级卷持久化操作的接口规范。
    """
    def __init__(self) -> None:
        """初始化超级卷仓储抽象基类。"""
        pass

    @abstractmethod
    def is_exist(self, super_volume: SuperVolume | str) -> bool:
        """检查超级卷是否已存在于仓储中。

        Args:
            super_volume: 超级卷实例或序列号。

        Returns:
            True 表示已存在，False 表示不存在。
        """
        pass

    @abstractmethod
    def reg_super_volume(self, super_volume: SuperVolume) -> None:
        """注册（新增）超级卷到仓储。

        Args:
            super_volume: 待注册的超级卷实例。
        """
        pass

    @abstractmethod
    def get_super_volume(self, super_volume_serial: str) -> SuperVolume:
        """根据序列号获取超级卷。

        Args:
            super_volume_serial: 超级卷序列号。

        Returns:
            对应的 SuperVolume 实例。
        """
        pass

    @abstractmethod
    def list_super_volume(self) -> list[SuperVolume]:
        """列出仓储中所有超级卷。

        Returns:
            超级卷实例列表。
        """
        pass

    @abstractmethod
    def add_volumes(
        self,
        structures: list[SuperVolumeStructure],
    ) -> None:
        """向已存在的超级卷添加一批子卷关联。

        Args:
            structures: 超级卷-子卷关联关系对象列表。
        """
        pass

    @abstractmethod
    def update_super_volume(self, serial: str, **fields) -> None:
        """更新超级卷指定字段。

        Args:
            serial: 要更新的超级卷序列号。
            **fields: 字段名到新值的映射。
        """
        pass

    @abstractmethod
    def update_super_volume_serial(self, old_serial: str, new_serial: str) -> None:
        """重置超级卷序列号，同步更新关联表中的外键引用。

        需要同步迁移：
        - super_volume_structures.super_volume_id（作为父时的子卷关联）

        Args:
            old_serial: 原超级卷序列号。
            new_serial: 新超级卷序列号。
        """
        pass

    @abstractmethod
    def remove_volumes(
        self,
        super_volume_serial: str,
        volume_ids: list[str],
    ) -> None:
        """从超级卷移除一批子卷（将关联标记为 UNUSED）。

        Args:
            super_volume_serial: 超级卷序列号。
            volume_ids: 待移除的子卷序列号列表。
        """
        pass

    @abstractmethod
    def remove_super_volume(self, serial: str) -> None:
        """将超级卷标记为 REMOVED（软删除），并释放其 USING 子卷关联。

        Args:
            serial: 超级卷序列号。
        """
        pass
