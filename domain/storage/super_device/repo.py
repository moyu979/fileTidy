# CHECK: 待检查 - 领域层 SuperDevice 仓储接口 - 超级设备持久化抽象

from abc import ABC, abstractmethod
from datetime import datetime

from domain.storage.device.base import Device
from domain.storage.super_device.base import SuperDevice


class super_device_repository_abc(ABC):
    """超级设备仓储抽象基类。

    定义超级设备持久化操作的接口规范，包括子设备的管理（新增、替换、移除）。
    """
    def __init__(self) -> None:
        """初始化超级设备仓储抽象基类。"""
        pass

    @abstractmethod
    def is_exist(self, device: Device | str) -> bool:
        """检查设备或超级设备是否已存在于仓储中。

        Args:
            device: 设备实例或设备序列号。

        Returns:
            True 表示已存在，False 表示不存在。
        """
        pass

    @abstractmethod
    def reg_super_device(self, super_device: SuperDevice) -> None:
        """注册（新增）超级设备到仓储。

        落库前校验每个子项独占（未被其它超级设备 USING 占用）与实体可用性，
        违反时抛出领域错误（SubDeviceInUseError / SubDeviceUnavailableError / SubDeviceNotFoundError）。

        Args:
            super_device: 待注册的超级设备实例。
        """
        pass

    @abstractmethod
    def get_super_device(self, super_device_serial: str) -> SuperDevice:
        """根据序列号获取超级设备。

        Args:
            super_device_serial: 超级设备序列号。

        Returns:
            对应的 SuperDevice 实例。
        """
        pass

    @abstractmethod
    def list_super_device(self) -> list[SuperDevice]:
        """列出仓储中所有超级设备。

        Returns:
            超级设备实例列表。
        """
        pass

    @abstractmethod
    def update_super_device(self, serial: str, **fields) -> None:
        """更新超级设备指定字段。

        Args:
            serial: 要更新的超级设备序列号。
            **fields: 字段名到新值的映射。
        """
        pass

    @abstractmethod
    def update_super_device_serial(self, old_serial: str, new_serial: str) -> None:
        """重置超级设备序列号，同步更新关联表中的外键引用。

        需要同步迁移：
        - super_device_structures.super_device_id（作为父时的子项关联）
        - super_device_structures.sub_device_id（作为子项被层叠引用）
        - volumes.device_id（卷建立在超级设备上）

        Args:
            old_serial: 原超级设备序列号。
            new_serial: 新超级设备序列号。
        """
        pass

    @abstractmethod
    def add_device(self, super_device_serial: str, device_serial: str, add_time: datetime) -> None:
        """向超级设备新增一个子设备。

        挂载前校验子项独占（未被其它超级设备 USING 占用）与实体可用性，
        违反时抛出领域错误（SubDeviceInUseError / SubDeviceUnavailableError / SubDeviceNotFoundError）。
        子项可为 device 或 super_device（支持层叠）。

        Args:
            super_device_serial: 超级设备序列号。
            device_serial: 待新增的子设备序列号。
            add_time: 添加时间。
        """
        pass

    @abstractmethod
    def replace_device(
        self, super_device_serial: str, old_device_serial: str,
        new_device_serial: str, add_time: datetime,
    ) -> None:
        """替换超级设备的子设备。

        旧设备标记 UNUSED + 记录 replaced_by，新设备新增 USING。
        新设备挂载前同样校验独占与实体可用性（SubDeviceInUseError / SubDeviceUnavailableError / SubDeviceNotFoundError）。

        Args:
            super_device_serial: 超级设备序列号。
            old_device_serial: 被替换的旧设备序列号。
            new_device_serial: 替换后的新设备序列号。
            add_time: 替换时间。
        """
        pass

    @abstractmethod
    def remove_device(self, super_device_serial: str, device_serial: str) -> None:
        """从超级设备移除一个子设备（标记 UNUSED）。

        Args:
            super_device_serial: 超级设备序列号。
            device_serial: 待移除的子设备序列号。
        """
        pass

    @abstractmethod
    def remove_super_device(self, serial: str) -> None:
        """将超级设备标记为 REMOVED（软删除），保留记录。

        移除前检查超级设备是否仍被引用：
        - 作为其他超级设备的子设备（super_device_structures sub_device_id state=USING，层叠）
        - 仍有未移除的卷建立在其上（volumes device_id state != REMOVED）
        存在任意引用则抛出 SuperDeviceInUseError，不执行移除。

        Args:
            serial: 超级设备序列号。
        """
        pass