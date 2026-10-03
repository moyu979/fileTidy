# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 SuperVolume 仓储接口 - 超级卷持久化抽象

from abc import ABC, abstractmethod
from datetime import datetime

from domain.storage.super_volume.base import SuperVolume
# TODO(P1): 批量 add_volumes 停用中 —— SuperVolumeStructure 仅其使用，恢复时一并取消注释
# from domain.storage.super_volume.structure import SuperVolumeStructure


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
    def add_volume(self, super_volume_serial: str, volume_id: str, add_time: datetime) -> None:
        """向超级卷新增一个子卷。

        挂载前校验子卷独占（未被其它超级卷 USING 占用）与实体可用性，
        违反时抛出领域错误（SubVolumeInUseError / SubVolumeUnavailableError / SubVolumeNotFoundError）。

        Args:
            super_volume_serial: 超级卷序列号。
            volume_id: 待新增的子卷序列号。
            add_time: 添加时间。
        """
        pass

    # TODO(P1): 批量 add_volumes 与 device 侧 add_device 不对称（device 只逐个新增），
    #   已停用；改由单个 add_volume 与 add_device 对齐。恢复批量能力时取消下面注释。
    #
    # @abstractmethod
    # def add_volumes(
    #     self,
    #     structures: list[SuperVolumeStructure],
    # ) -> None:
    #     """向已存在的超级卷添加一批子卷关联。
    #
    #     Note:
    #         当前实现会拒绝「曾属于任何超级卷的卷」再次编入（包括关系已退役为
    #         REPLACED 的），这是 `super_volume_structures.volume_id` 硬唯一约束造成的
    #         妥协，已知语义过强，见 models.py 该列的 TODO(P2)。
    #
    #     Args:
    #         structures: 超级卷-子卷关联关系对象列表。
    #     """
    #     pass

    @abstractmethod
    def replace_volume(
        self, super_volume_serial: str, old_volume_id: str,
        new_volume_id: str, add_time: datetime,
    ) -> None:
        """替换超级卷中的一个子卷。

        旧卷关联标记 REPLACED（退役，不随复活恢复）+ 记录 replaced_by，新卷新增 USING。
        新卷挂载前同样校验独占与实体可用性。

        Args:
            super_volume_serial: 超级卷序列号。
            old_volume_id: 被替换的旧子卷序列号。
            new_volume_id: 替换后的新子卷序列号。
            add_time: 替换时间。

        Raises:
            ValueError: 旧子卷不在该超级卷的 USING 成员中。
            SubVolumeInUseError: 新子卷已被其它超级卷以 USING 占用。
            SubVolumeNotFoundError: 新子卷不是已登记的 volume。
            SubVolumeUnavailableError: 新子卷处于 REMOVED/FAULT 不可用状态。
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

    # TODO(P1): 「摘子卷」功能暂缓（与 device 侧同口径停用）—— 当前没有配套的数据迁移，
    #   直接摘除会破坏阵列编成（copy / snapraid_raid5 的成员数不变量、换盘重建均未实现）；
    #   且 `super_volume_structures.volume_id` 上的硬唯一约束会让被摘子卷无法再编入任何超级卷。
    #   恢复时取消下面注释（ABC 必须与 infra 实现同步启用/停用）。
    #
    # @abstractmethod
    # def remove_volumes(
    #     self,
    #     super_volume_serial: str,
    #     volume_ids: list[str],
    # ) -> None:
    #     """从超级卷移除一批子卷（将关联标记为 REPLACED）。
    #
    #     Args:
    #         super_volume_serial: 超级卷序列号。
    #         volume_ids: 待移除的子卷序列号列表。
    #     """
    #     pass

    @abstractmethod
    def remove_super_volume(self, serial: str) -> None:
        """将超级卷标记为 REMOVED（软删除），并释放其 USING 子卷关联。

        移除成功时，会把本超级卷名下的子卷关联行（state == USING）一并置为
        SUPER_VOLUME_REMOVED，释放这些子卷；该状态区别于成员侧退役的 REPLACED
        （`replace_volume`），使 `revive_super_volume` 能精确恢复本方法释放的关联。

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
        `replace_volume` 换下的旧卷（state == REPLACED）**不**恢复。

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
