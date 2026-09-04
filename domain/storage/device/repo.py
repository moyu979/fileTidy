# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: ai生成，待检查 - 领域层 Device 仓储接口 - 设备持久化抽象

from abc import ABC, abstractmethod

from domain.storage.device.base import Device


class DeviceRepositoryABC(ABC):
    """设备仓储抽象基类。

    定义设备持久化操作的接口规范，所有具体设备仓储实现需继承此类。
    """
    def __init__(self) -> None:
        """初始化仓储抽象基类。"""
        pass

    @abstractmethod
    def is_exist(self, device: Device | str) -> bool:
        """检查设备是否已存在于仓储中。

        Args:
            device: 待检查的设备实例或设备序列号。

        Returns:
            True 表示设备已存在，False 表示不存在。
        """
        pass

    @abstractmethod
    def reg_device(self, device: Device) -> None:
        """注册（新增）设备到仓储。

        Args:
            device: 待注册的设备实例。
        """
        pass

    @abstractmethod
    def get_device(self, serial: str) -> Device | None:
        """根据序列号获取设备。

        Args:
            serial: 设备序列号。

        Returns:
            对应的 Device 实例，不存在时返回 None。
        """
        pass

    @abstractmethod
    def list_devices(self) -> list[Device]:
        """列出仓储中所有设备。

        Returns:
            设备实例列表。
        """
        pass

    @abstractmethod
    def update_device(self, serial: str, **fields) -> None:
        """更新设备指定字段。

        Args:
            serial: 要更新的设备序列号。
            **fields: 字段名到新值的映射。
        """
        pass

    @abstractmethod
    def update_serial(self, old_serial: str, new_serial: str) -> None:
        """重置设备序列号，同步更新关联表中的外键引用。

        Args:
            old_serial: 原设备序列号。
            new_serial: 新设备序列号。
        """
        pass

    @abstractmethod
    def remove_device(self, serial: str) -> None:
        """将设备标记为 REMOVED（软删除），保留记录。

        移除前检查设备是否仍被引用：
        - 作为超级设备的子设备（super_device_structures state=USING）
        - 仍有未移除的卷建立在其上（volumes state != REMOVED）
        存在任意引用则抛出 DeviceInUseError，不执行移除。

        Args:
            serial: 设备序列号。

        Raises:
            DeviceInUseError: 设备仍被引用时抛出。
        """
        pass