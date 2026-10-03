# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 Volume 仓储接口 - 卷持久化抽象
# NOTE: file 子系统未完成（设计未定稿）：remove_volume 中关于 file_locations 的引用检查为临时方案，
#       待 file 模块重新设计后可能摘除。

from abc import ABC, abstractmethod

from domain.storage.volume.base import Volume


class VolumeRepositoryABC(ABC):
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

        注册前会校验 device_id 是否为有效且可用的 Device 或 SuperDevice。

        Args:
            volume: 待注册的卷实例。

        Raises:
            VolumeAlreadyRegisteredError: 该 serial 已被一条非 REMOVED 的行占用。
            VolumeAlreadyRemovedError: 该 serial 被一条 REMOVED（软删除）行占位，需先复活。
            ValueError: device_id 既不是有效 Device 也不是有效 SuperDevice，
                或对应的实体处于 REMOVED / FAULT 不可用状态。
        """
        pass

    @abstractmethod
    def get_volume(self, serial: str, exclude_removed: bool = True) -> Volume | None:
        """根据卷 ID 加载卷。

        Args:
            serial: 卷的序列号。
            exclude_removed: 为 True（默认）时，已移除（state == REMOVED）的卷视为不存在。

        Returns:
            对应的 Volume 实例，不存在时返回 None。
        """
        pass

    @abstractmethod
    def list_volumes(self, exclude_removed: bool = True) -> list[Volume]:
        """列出仓储中的卷。

        Args:
            exclude_removed: 为 True（默认）时排除已移除（state == REMOVED）的卷。

        Returns:
            卷实例列表。
        """
        pass

    @abstractmethod
    def update_volume(self, serial: str, /, **fields) -> None:
        """更新卷指定字段。

        可更新字段自动取自 VolumeModel 的列（主键 serial 除外），未知字段会报错。

        Note:
            `serial` 是位置参数（positional-only），不能作为关键字传入；序列号不可经本方法
            修改（会直接报错），改名请走 `update_serial`（会同步迁移关联表引用）。
            置为 REMOVED 也请走 `remove_volume`（带引用校验）。

        Args:
            serial: 要更新的卷序列号（位置参数）。
            **fields: 字段名到新值的映射；None 表示不修改该字段。
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

        Note:
            置为 REMOVED 只能走本方法，不要用 `update_volume(state=REMOVED)`
            —— 仓储层会直接拒绝，那样会绕过上面的引用校验。
            被移除的卷可经 `revive_volume` 复活（state 置回 UNKNOWN）；复活前，
            同一 serial 不能再登记（serial 是主键，行仍占位）。

        Args:
            serial: 卷序列号。

        Raises:
            VolumeNotFoundError: 卷不存在。
            VolumeAlreadyRemovedError: 卷已处于 REMOVED（不可重复移除）。
            VolumeInUseError: 卷仍被引用时抛出。
        """
        pass

    @abstractmethod
    def revive_volume(self, serial: str) -> None:
        """复活已移除（REMOVED）的卷：原地把 state 置回 UNKNOWN。

        复活是可逆软删除的逆操作：行原地 UPDATE（serial 是主键，不能重新 INSERT），
        其余字段保持删除前的值不变（不刷新 name / capacity / info / 时间）。

        前置校验：
        - 目标必须存在；否则抛 VolumeNotFoundError。
        - 目标必须处于 REMOVED；否则抛 VolumeNotRemovedError（未移除的卷无需复活）。
        - 卷的挂载对象（`device_id` 指向的 Device 或 SuperDevice）必须仍存在且可用；
          否则抛 ValueError（与 reg / update 同口径）。

        **不校验卷自身是否被引用**：被引用的卷进不了 REMOVED（`remove_volume` 用
        VolumeInUseError 把关），故「REMOVED 且仍被引用」属并发 / 手工改库的脏状态，
        而复活正是其修复手段 —— 复活后 state 与引用关系重新自洽。

        Args:
            serial: 卷序列号。

        Raises:
            VolumeNotFoundError: 卷不存在。
            VolumeNotRemovedError: 卷未处于 REMOVED（无需复活）。
            ValueError: 挂载对象（Device / SuperDevice）不存在或不可用。
        """
        pass
