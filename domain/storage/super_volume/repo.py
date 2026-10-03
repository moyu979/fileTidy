# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 SuperVolume 仓储接口 - 超级卷持久化抽象

from abc import ABC, abstractmethod

from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.structure import SuperVolumeStructure


class SuperVolumeRepositoryABC(ABC):
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

        主行与其全部子卷关联行在同一事务内提交；子卷须存在且可用。

        Args:
            super_volume: 待注册的超级卷实例。

        Raises:
            SuperVolumeAlreadyRegisteredError: 该 serial 已被一条非 REMOVED 的行占用。
            SuperVolumeAlreadyRemovedError: 该 serial 被一条 REMOVED（软删除）行占位，需先复活。
            SubVolumeInUseError / SubVolumeNotFoundError / SubVolumeUnavailableError:
                任一子卷不满足独占 / 存在 / 可用。
        """
        pass

    @abstractmethod
    def get_super_volume(
        self, super_volume_serial: str, exclude_removed: bool = True
    ) -> SuperVolume | None:
        """根据序列号获取超级卷。

        Args:
            super_volume_serial: 超级卷序列号。
            exclude_removed: 为 True（默认）时，已移除（state == REMOVED）的超级卷视为不存在。

        Returns:
            对应的 SuperVolume 实例；不存在时返回 None。
        """
        pass

    @abstractmethod
    def list_super_volume(self, exclude_removed: bool = True) -> list[SuperVolume]:
        """列出仓储中所有超级卷。

        Args:
            exclude_removed: 为 True（默认）时排除已移除（state == REMOVED）的超级卷。

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

        Note:
            当前实现会拒绝「曾属于任何超级卷的卷」再次编入（包括关系已退役为
            UNUSED 的），这是 `super_volume_structures.volume_id` 硬唯一约束造成的
            妥协，已知语义过强，见 models.py 该列的 TODO(P2)。

        Args:
            structures: 超级卷-子卷关联关系对象列表。
        """
        pass

    @abstractmethod
    def update_super_volume(self, serial: str, /, **fields) -> None:
        """更新超级卷指定字段。

        可更新字段自动取自 SuperVolumeModel 的列（主键 serial 除外），未知字段会报错。

        Note:
            `serial` 是位置参数（positional-only），不能作为关键字传入；序列号不可经本方法
            修改（会直接报错），改名请走 `update_super_volume_serial`（会同步迁移关联表引用）。
            置为 REMOVED 也请走 `remove_super_volume`（带引用校验）。

        Args:
            serial: 要更新的超级卷序列号（位置参数）。
            **fields: 字段名到新值的映射；None 表示不修改该字段。
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

        移除成功时，会把本超级卷名下的子卷关联行（state == USING）一并置为
        SUPER_VOLUME_REMOVED，释放这些子卷；该状态区别于「成员被移除」的 UNUSED，
        使 `revive_super_volume` 能精确恢复本方法释放的关联。

        Args:
            serial: 超级卷序列号。

        Raises:
            SuperVolumeNotFoundError: 超级卷不存在。
            SuperVolumeAlreadyRemovedError: 超级卷已处于 REMOVED（不可重复移除）。
        """
        pass

    @abstractmethod
    def revive_super_volume(self, serial: str) -> None:
        """复活已移除（REMOVED）的超级卷：原地把 state 置回 UNKNOWN。

        复活是可逆软删除的逆操作：行原地 UPDATE（serial 是主键，不能重新 INSERT），
        其余字段保持删除前的值不变。目标状态为 UNKNOWN（复活 ≠ 立即可用）。

        拓扑一并恢复：把 `remove_super_volume` 释放掉的那批子卷关联行
        （state == SUPER_VOLUME_REMOVED）重新置回 USING；
        `remove_volumes` 摘除的成员（state == UNUSED）**不**恢复。

        前置校验（任一失败均抛异常，事务整体回滚）：
        - 目标存在、且正处于 REMOVED；
        - 待恢复的每个子卷都未被他处占用且可用 → 透传 SubVolumeInUseError /
          SubVolumeUnavailableError / SubVolumeNotFoundError。

        Args:
            serial: 超级卷序列号。

        Raises:
            SuperVolumeNotFoundError: 超级卷不存在。
            SuperVolumeNotRemovedError: 超级卷未处于 REMOVED（无需复活）。
            SubVolumeInUseError: 待恢复的子卷已被其它超级卷占用。
            SubVolumeUnavailableError: 待恢复的子卷已 REMOVED / FAULT。
            SubVolumeNotFoundError: 待恢复的子卷不存在。
        """
        pass
