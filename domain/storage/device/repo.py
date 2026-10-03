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

        Raises:
            DeviceAlreadyRegisteredError: 该 serial 已被一条非 REMOVED 的行占用。
            DeviceAlreadyRemovedError: 该 serial 被一条 REMOVED（软删除）行占位，需先复活。
        """
        pass

    @abstractmethod
    def get_device(self, serial: str, exclude_removed: bool = True) -> Device | None:
        """根据序列号获取设备。

        Args:
            serial: 设备序列号。
            exclude_removed: 为 True（默认）时，已移除（state == REMOVED）的设备视为不存在。

        Returns:
            对应的 Device 实例，不存在时返回 None。
        """
        pass

    @abstractmethod
    def list_devices(self, exclude_removed: bool = True) -> list[Device]:
        """列出仓储中的设备。

        Args:
            exclude_removed: 为 True（默认）时排除已移除（state == REMOVED）的设备。

        Returns:
            设备实例列表。
        """
        pass

    @abstractmethod
    def update_device(self, serial: str, /, **fields) -> None:
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

        Note:
            置为 REMOVED 只能走本方法，不要用 `update_device(state=REMOVED)`
            —— 仓储层会直接拒绝，那样会绕过上面的引用校验。
            被移除的设备可经 `revive_device` 复活（state 置回 UNKNOWN）；复活前，
            同一 serial 不能再登记（serial 是主键，行仍占位）。

        Args:
            serial: 设备序列号。

        Raises:
            DeviceNotFoundError: 设备不存在。
            DeviceAlreadyRemovedError: 设备已处于 REMOVED（不可重复移除）。
            DeviceInUseError: 设备仍被引用时抛出。
        """
        pass

    @abstractmethod
    def revive_device(self, serial: str) -> None:
        """复活已移除（REMOVED）的设备：原地把 state 置回 UNKNOWN。

        复活是可逆软删除的逆操作：行原地 UPDATE（serial 是主键，不能重新 INSERT），
        其余字段保持删除前的值不变（不刷新 name / capacity / info / 时间）。
        复活不等于立即可用：目标状态为 UNKNOWN，待一次健康检查再进入 HEALTHY / FAULT。

        前置校验：
        - 目标必须存在；否则抛 DeviceNotFoundError。
        - 目标必须处于 REMOVED；否则抛 DeviceNotRemovedError（未移除的设备无需复活）。

        **不校验是否被引用**：被引用的设备进不了 REMOVED（`remove_device` 用
        DeviceInUseError 把关），故「REMOVED 且仍被引用」属并发 / 手工改库的脏状态，
        而复活正是其修复手段 —— 复活后 state 与引用关系重新自洽。

        Args:
            serial: 设备序列号。

        Raises:
            DeviceNotFoundError: 设备不存在。
            DeviceNotRemovedError: 设备未处于 REMOVED（无需复活）。
        """
        pass