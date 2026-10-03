# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 SuperDevice 仓储接口 - 超级设备持久化抽象

from abc import ABC, abstractmethod
from datetime import datetime

from domain.storage.super_device.base import SuperDevice


class SuperDeviceRepositoryABC(ABC):
    """超级设备仓储抽象基类。

    定义超级设备持久化操作的接口规范，包括子设备的管理（新增、替换、移除）。
    """
    def __init__(self) -> None:
        """初始化超级设备仓储抽象基类。"""
        pass

    @abstractmethod
    def is_exist(self, super_device: SuperDevice | str) -> bool:
        """检查超级设备是否已存在于仓储中。

        Args:
            super_device: 超级设备实例或超级设备序列号。

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

        Raises:
            SuperDeviceAlreadyRegisteredError: 该 serial 已被一条非 REMOVED 的行占用。
            SuperDeviceAlreadyRemovedError: 该 serial 被一条 REMOVED（软删除）行占位，需先复活。
        """
        pass

    @abstractmethod
    def get_super_device(
        self, super_device_serial: str, exclude_removed: bool = True
    ) -> SuperDevice | None:
        """根据序列号获取超级设备。

        Args:
            super_device_serial: 超级设备序列号。
            exclude_removed: 为 True（默认）时，已移除（state == REMOVED）的超级设备视为不存在。

        Returns:
            对应的 SuperDevice 实例，不存在时返回 None。
        """
        pass

    @abstractmethod
    def list_super_device(self, exclude_removed: bool = True) -> list[SuperDevice]:
        """列出仓储中的超级设备。

        Args:
            exclude_removed: 为 True（默认）时排除已移除（state == REMOVED）的超级设备。

        Returns:
            超级设备实例列表。
        """
        pass

    @abstractmethod
    def update_super_device(self, serial: str, /, **fields) -> None:
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

        旧设备标记 REPLACED（换盘退役，不随复活恢复）+ 记录 replaced_by，新设备新增 USING。
        新设备挂载前同样校验独占与实体可用性（SubDeviceInUseError / SubDeviceUnavailableError / SubDeviceNotFoundError）。

        Args:
            super_device_serial: 超级设备序列号。
            old_device_serial: 被替换的旧设备序列号。
            new_device_serial: 替换后的新设备序列号。
            add_time: 替换时间。
        """
        pass

    # TODO(P1): 「摘子项」功能暂缓（未保证 SingleSuperDevice 的 1 子项不变量）。
    #   恢复时取消下面注释（ABC 必须与 infra 实现同步启用/停用）。
    #
    # @abstractmethod
    # def remove_device(self, super_device_serial: str, device_serial: str) -> None:
    #     """从超级设备移除一个子设备（标记 UNUSED）。
    #
    #     Args:
    #         super_device_serial: 超级设备序列号。
    #         device_serial: 待移除的子设备序列号。
    #     """
    #     pass

    @abstractmethod
    def remove_super_device(self, serial: str) -> None:
        """将超级设备标记为 REMOVED（软删除），保留记录。

        移除前检查超级设备是否仍被引用：
        - 作为其他超级设备的子设备（super_device_structures sub_device_id state=USING，层叠）
        - 仍有未移除的卷建立在其上（volumes device_id state != REMOVED）
        存在任意引用则抛出 SuperDeviceInUseError，不执行移除。

        移除成功时，本超级设备名下的子项关联行（super_device_id == serial 且 state=USING）
        一并标记为 SUPER_DEVICE_REMOVED，释放这些子项（与 remove_device 同口径）；
        用独立状态（而非笼统的退役态）与「换盘退役（REPLACED）」区分，
        使 revive_super_device 能精确恢复本方法释放的关联，而不误复活换掉的盘。

        Note:
            置为 REMOVED 只能走本方法，不要用 `update_super_device(state=REMOVED)`
            —— 仓储层会直接拒绝，那样会绕过上面的引用校验。
            被移除的超级设备可经 `revive_super_device` 复活（state 置回 UNKNOWN，拓扑一并恢复）。

        Args:
            serial: 超级设备序列号。

        Raises:
            SuperDeviceNotFoundError: 超级设备不存在。
            SuperDeviceAlreadyRemovedError: 超级设备已处于 REMOVED（不可重复移除）。
            SuperDeviceInUseError: 超级设备仍被引用时抛出。
        """
        pass

    @abstractmethod
    def revive_super_device(self, serial: str) -> None:
        """复活已移除（REMOVED）的超级设备：原地把 state 置回 UNKNOWN。

        复活是可逆软删除的逆操作：行原地 UPDATE（serial 是主键，不能重新 INSERT），
        其余字段保持删除前的值不变。复活不等于立即可用：目标状态为 UNKNOWN，
        待一次健康检查再进入 HEALTHY / FAULT / DEGRADING。

        拓扑一并恢复：`remove_super_device` 释放掉的那批子项关联行（state == SUPER_DEVICE_REMOVED）
        重新置回 USING；`replace_device` 换下来的旧子项（state == REPLACED）不恢复。

        前置校验（任一失败均抛异常，并整体回滚）：
        - 目标必须存在；否则抛 ValueError。
        - 目标必须处于 REMOVED；否则抛 SuperDeviceNotRemovedError（未移除的超级设备无需复活）。
        - **不校验目标自身是否被引用**：被引用的超级设备进不了 REMOVED（`remove_super_device`
          用 SuperDeviceInUseError 把关），故那是脏库情形，而复活正是其修复手段。
        - 待恢复的每个子项都不得被其它超级设备 USING 占用、且实体可用；
          否则透传 SubDeviceInUseError / SubDeviceUnavailableError / SubDeviceNotFoundError。

        Args:
            serial: 超级设备序列号。

        Raises:
            SuperDeviceNotFoundError: 超级设备不存在。
            SuperDeviceNotRemovedError: 超级设备未处于 REMOVED（无需复活）。
            SubDeviceInUseError: 待恢复的子项已被其它超级设备占用。
            SubDeviceUnavailableError: 待恢复的子项实体已 REMOVED / FAULT。
        """
        pass