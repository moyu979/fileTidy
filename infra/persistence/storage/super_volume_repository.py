import logging
from typing import Any

from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.enum import (
    SuperVolumeRelationState,
    SuperVolumeState,
)
from domain.storage.super_volume.errors import (
    SubVolumeInUseError,
    SubVolumeNotFoundError,
    SubVolumeUnavailableError,
    SuperVolumeAlreadyRegisteredError,
    SuperVolumeAlreadyRemovedError,
    SuperVolumeNotFoundError,
    SuperVolumeNotRemovedError,
)
from domain.storage.super_volume.repo import SuperVolumeRepositoryABC
from domain.storage.super_volume.structure import SuperVolumeStructure
from domain.storage.volume.enum import UNAVAILABLE_VOLUME_STATES
from infra.persistence._enum_utils import coerce_enum
from infra.persistence._model_utils import updatable_fields
from infra.persistence.database import session_scope
from infra.persistence.models import (
    SuperVolumeModel,
    SuperVolumeStructureModel,
    VolumeModel,
)

logger = logging.getLogger(__name__)


def _ensure_sub_volume_available(session, volume_id: str) -> None:
    """
    校验子卷可挂载：独占（未被其它超级卷以 USING 占用）+ 实体可用（非 REMOVED/FAULT）。

    Args:
        session: SQLAlchemy 会话
        volume_id: 子卷序列号

    Raises:
        SubVolumeInUseError: 子卷已被其它超级卷以 USING 占用
        SubVolumeNotFoundError: 子卷不是已登记的 volume
        SubVolumeUnavailableError: 子卷处于 REMOVED/FAULT 不可用状态
    """
    holder = (
        session.query(SuperVolumeStructureModel)
        .filter(
            SuperVolumeStructureModel.volume_id == volume_id,
            SuperVolumeStructureModel.state == SuperVolumeRelationState.USING,
        )
        .first()
    )
    if holder is not None:
        raise SubVolumeInUseError(volume_id, holder.super_volume_id)

    volume = (
        session.query(VolumeModel)
        .filter(VolumeModel.serial == volume_id)
        .first()
    )
    if volume is None:
        raise SubVolumeNotFoundError(volume_id)
    if volume.state in UNAVAILABLE_VOLUME_STATES:
        raise SubVolumeUnavailableError(volume_id, volume.state)


class SuperVolumeRepository(SuperVolumeRepositoryABC):
    """超级卷仓库实现，提供超级卷数据的持久化存储和查询操作。"""

    def __init__(self, session_factory) -> None:
        """
        初始化 SuperVolumeRepository。

        Args:
            session_factory: 用于创建 SQLAlchemy 会话的工厂
        """
        self.session_factory = session_factory
        super().__init__()
        logger.info("SuperVolumeRepository constructed")

    def is_exist(self, super_volume: SuperVolume | str) -> bool:
        """
        判断超级卷是否已存在于数据库中。

        Args:
            super_volume: 超级卷对象或序列号字符串

        Returns:
            存在返回 True，否则返回 False
        """
        if isinstance(super_volume, SuperVolume):
            serial = super_volume.serial
        else:
            serial = super_volume
        with session_scope(self.session_factory) as session:
            return session.query(SuperVolumeModel).filter(SuperVolumeModel.serial == serial).first() is not None

    def reg_super_volume(self, super_volume: SuperVolume) -> None:
        """
        注册一个新的超级卷及其关联的卷结构。

        超级卷主行与其全部子卷关联行在同一事务内提交，
        避免「超级卷已落库、关联行写入失败」产生的脏数据。

        注册前校验每个子卷：存在、可用（非 REMOVED/FAULT）、且未被其它超级卷以 USING 占用。

        Args:
            super_volume: 要注册的超级卷对象

        Raises:
            SuperVolumeAlreadyRegisteredError: 该 serial 已被一条非 REMOVED 的行占用
            SuperVolumeAlreadyRemovedError: 该 serial 被一条 REMOVED（软删除）行占位，需先复活
            SubVolumeInUseError / SubVolumeNotFoundError / SubVolumeUnavailableError:
                任一子卷不满足独占 / 存在 / 可用
        """
        super_volume_model = SuperVolumeModel(
            serial=super_volume.serial,
            name=super_volume.name,
            svtype=super_volume.svtype,
            method=super_volume.method,
            add_time=super_volume.add_time,
            last_check_time=super_volume.last_check_time,
            state=coerce_enum(SuperVolumeState, super_volume.state),
            info=super_volume.info,
        )
        structures = []
        for volume_id in super_volume.volumes:
            structure = SuperVolumeStructureModel(
                super_volume_id=super_volume.serial,
                volume_id=volume_id,
                add_time=super_volume.add_time,
                state=SuperVolumeRelationState.USING,
                info="",
            )
            structures.append(structure)
        with session_scope(self.session_factory) as session:
            # 唯一性预检：serial 是主键，任何已存在的行（含 REMOVED）都算占用。
            # 在这里判定（而不是让 INSERT 撞 PK），使调用方——含绕过 service 的——都能拿到
            # 结构化领域异常而非裸 IntegrityError。
            existing = (
                session.query(SuperVolumeModel)
                .filter(SuperVolumeModel.serial == super_volume.serial)
                .first()
            )
            if existing is not None:
                # 分类就在仓储完成：REMOVED 行占位 与 活跃占用 是互斥的两种事实，
                # 各给一个异常类型，上层不必再自己看 state 分流。
                if existing.state == SuperVolumeState.REMOVED:
                    raise SuperVolumeAlreadyRemovedError(super_volume.serial)
                raise SuperVolumeAlreadyRegisteredError(
                    super_volume.serial, state=existing.state
                )
            # 挂载前校验每个子卷：独占（未被其它超级卷 USING 占用）+ 实体可用
            for volume_id in super_volume.volumes:
                _ensure_sub_volume_available(session, volume_id)
            session.add(super_volume_model)
            session.add_all(structures)
            # 显式提交（与 device/volume 仓储一致）；session_scope 退出时的提交为幂等兜底
            session.commit()

    @staticmethod
    def _model_to_dict(model: SuperVolumeModel, volume_ids: list[str]) -> dict[str, Any]:
        """
        将 SuperVolumeModel 转换为字典。

        Args:
            model: SuperVolumeModel 实例
            volume_ids: 关联的卷序列号列表

        Returns:
            包含所有字段的字典
        """
        return {
            "serial": model.serial,
            "name": model.name,
            "svtype": model.svtype,
            "method": model.method,
            "add_time": model.add_time,
            "last_check_time": model.last_check_time,
            "state": model.state,
            "info": model.info,
            "volumes": volume_ids,
        }

    def get_super_volume(
        self, super_volume_serial: str, exclude_removed: bool = True
    ) -> SuperVolume | None:
        """
        根据序列号获取超级卷。

        Args:
            super_volume_serial: 超级卷序列号
            exclude_removed: 为 True（默认）时，已移除（REMOVED）的超级卷视为不存在

        Returns:
            超级卷对象，若不存在则返回 None
        """
        with session_scope(self.session_factory) as session:
            query = session.query(SuperVolumeModel).filter(
                SuperVolumeModel.serial == super_volume_serial
            )
            if exclude_removed:
                query = query.filter(SuperVolumeModel.state != SuperVolumeState.REMOVED)
            model = query.first()
            if model is None:
                return None
            structure_rows = session.query(SuperVolumeStructureModel).filter(
                SuperVolumeStructureModel.super_volume_id == super_volume_serial,
                SuperVolumeStructureModel.state == SuperVolumeRelationState.USING,
            ).all()
            volume_ids = [row.volume_id for row in structure_rows]
            data = self._model_to_dict(model, volume_ids)
            return SuperVolume.from_dict(data)

    def list_super_volume(self, exclude_removed: bool = True) -> list[SuperVolume]:
        """
        获取所有已注册的超级卷列表。

        Args:
            exclude_removed: 为 True（默认）时排除已移除（REMOVED）的超级卷。

        Returns:
            超级卷对象列表
        """
        with session_scope(self.session_factory) as session:
            query = session.query(SuperVolumeModel)
            if exclude_removed:
                query = query.filter(SuperVolumeModel.state != SuperVolumeState.REMOVED)
            models = query.all()
            result = []
            for model in models:
                structure_rows = session.query(SuperVolumeStructureModel).filter(
                    SuperVolumeStructureModel.super_volume_id == model.serial,
                    SuperVolumeStructureModel.state == SuperVolumeRelationState.USING,
                ).all()
                volume_ids = [row.volume_id for row in structure_rows]
                data = self._model_to_dict(model, volume_ids)
                result.append(SuperVolume.from_dict(data))
            return result

    def add_volumes(
        self,
        structures: list[SuperVolumeStructure],
    ) -> None:
        """
        批量添加卷到超级卷的关联结构中。

        添加前校验超级卷存在，且子卷尚未被任何超级卷关联（含 UNUSED，
        因为 super_volume_structures.volume_id 上有唯一约束）。
        TODO(P2): 「含 UNUSED 也算被占用」是 volume_id 硬唯一约束下的妥协
        （见 models.py 该列的 TODO）。若将来改成部分唯一索引（仅 USING 唯一），
        此处校验应放宽为「只拒绝仍处于 USING 的子卷」，让退役（UNUSED）的卷
        能被重新编入别的超级卷。
        Args:
            structures: 超级卷结构对象列表

        Raises:
            SuperVolumeNotFoundError: 超级卷不存在。
            ValueError: 子卷已被其他超级卷关联时抛出。
        """
        models = []
        with session_scope(self.session_factory) as session:
            for st in structures:
                parent = session.query(SuperVolumeModel).filter(
                    SuperVolumeModel.serial == st.super_volume_serial
                ).first()
                if parent is None:
                    raise SuperVolumeNotFoundError(st.super_volume_serial)
                existing = session.query(SuperVolumeStructureModel).filter(
                    SuperVolumeStructureModel.volume_id == st.volume_id
                ).first()
                if existing is not None:
                    raise ValueError(
                        f"卷 {st.volume_id} 已属于超级卷 {existing.super_volume_id}，无法重复添加"
                    )
                model = SuperVolumeStructureModel(
                    super_volume_id=st.super_volume_serial,
                    volume_id=st.volume_id,
                    add_time=st.add_time,
                    state=st.state,
                    info=st.info,
                )
                models.append(model)
            session.add_all(models)

    def update_super_volume(self, serial: str, /, **fields) -> None:
        """
        更新超级卷的指定字段。

        值为 None 的字段视为「未提供」，保持原值不变（区别于「清空」）。
        可更新字段自动取自 SuperVolumeModel 的列（主键 serial 除外），未知字段会报错，
        避免拼错键名时静默无效。

        Note:
            `serial` 是位置参数（positional-only），不能作为关键字传入；序列号不可经本方法
            修改（会直接报错），改名请走 `update_super_volume_serial`（会同步迁移关联表引用）。

        Args:
            serial: 超级卷序列号（位置参数）
            **fields: 要更新的字段名和值（领域字段名即模型属性名）；
                None 表示不修改该字段

        Raises:
            SuperVolumeNotFoundError: 超级卷不存在
            ValueError: 含未知字段；或试图修改 serial（须走 update_super_volume_serial）；
                或把 state 改为 REMOVED（软删除必须走 remove_super_volume，以免绕过引用校验）
        """
        with session_scope(self.session_factory) as session:
            model = (
                session.query(SuperVolumeModel)
                .filter(SuperVolumeModel.serial == serial)
                .first()
            )
            if model is None:
                raise SuperVolumeNotFoundError(serial)
            allowed = updatable_fields(SuperVolumeModel)
            for key, value in fields.items():
                if key == "serial":
                    # 改名必须走 update_super_volume_serial：它会同步迁移
                    # super_volume_structures.super_volume_id，通用通道不会。
                    raise ValueError(
                        f"super_volume {serial} 不允许通过 update_super_volume 修改序列号，"
                        f"请改用 update_super_volume_serial（会同步迁移关联表引用）"
                    )
                if key not in allowed:
                    raise ValueError(
                        f"super_volume {serial} 不支持更新字段 {key!r}；"
                        f"可更新字段：{', '.join(sorted(allowed))}"
                    )
                if value is None:  # None = 未提供该字段 → 保持原样
                    continue
                if key == "state":
                    value = coerce_enum(SuperVolumeState, value)
                    if value is SuperVolumeState.REMOVED:
                        raise ValueError(
                            f"super_volume {serial} 不允许通过 update_super_volume 置为 REMOVED，"
                            f"请改用 remove_super_volume（带引用校验）"
                        )
                setattr(model, key, value)
            session.commit()

    def update_super_volume_serial(self, old_serial: str, new_serial: str) -> None:
        """
        重置超级卷序列号，同步更新关联表中的外键引用。

        super_volumes.serial 是主键，被 super_volume_structures.super_volume_id
        外键引用。因不能直接删除被引用的旧主键行，采用
        「以 new_serial 复制新主键行 → 迁移引用 → 再删旧行」的方式。

        Args:
            old_serial: 原超级卷序列号
            new_serial: 新超级卷序列号

        Raises:
            SuperVolumeNotFoundError: 原超级卷不存在
            SuperVolumeAlreadyRemovedError: 新序列号被一条 REMOVED（软删除）行占位
            SuperVolumeAlreadyRegisteredError: 新序列号已被一条非 REMOVED 的行占用
        """
        with session_scope(self.session_factory) as session:
            row = (
                session.query(SuperVolumeModel)
                .filter(SuperVolumeModel.serial == old_serial)
                .first()
            )
            if row is None:
                raise SuperVolumeNotFoundError(old_serial)
            if old_serial == new_serial:
                return

            # 预检：目标 serial 是否已被占用。serial 是主键，任何已存在的行（含 REMOVED 墓碑）
            # 都算占用；不预检的话，下面复制新主键行会在 flush 时撞 PK 抛裸 IntegrityError。
            # 分类与 reg_super_volume 同口径：墓碑 → AlreadyRemoved，活跃 → AlreadyRegistered。
            conflict = (
                session.query(SuperVolumeModel)
                .filter(SuperVolumeModel.serial == new_serial)
                .first()
            )
            if conflict is not None:
                if conflict.state == SuperVolumeState.REMOVED:
                    raise SuperVolumeAlreadyRemovedError(new_serial)
                raise SuperVolumeAlreadyRegisteredError(
                    new_serial, state=conflict.state
                )

            # 1. 以 new_serial 复制主键行（先让新主键存在，FK 才能指向它）
            new_row = SuperVolumeModel(
                serial=new_serial,
                name=row.name,
                svtype=row.svtype,
                method=row.method,
                add_time=row.add_time,
                last_check_time=row.last_check_time,
                state=row.state,
                info=row.info,
            )
            session.add(new_row)
            session.flush()

            # 2. 迁移关联表：super_volume_id old → new
            session.query(SuperVolumeStructureModel).filter(
                SuperVolumeStructureModel.super_volume_id == old_serial
            ).update({"super_volume_id": new_serial})

            # 3. 删除旧主键行
            session.delete(row)
            session.commit()

    def remove_volumes(
        self,
        super_volume_serial: str,
        volume_ids: list[str],
    ) -> None:
        """
        从超级卷移除一批子卷（将 USING 关联标记为 UNUSED）。

        Args:
            super_volume_serial: 超级卷序列号
            volume_ids: 待移除的子卷序列号列表

        Raises:
            SuperVolumeNotFoundError: 超级卷不存在。
            ValueError: 存在非 USING 成员卷时抛出（不部分更新）。
        """
        with session_scope(self.session_factory) as session:
            parent = session.query(SuperVolumeModel).filter(
                SuperVolumeModel.serial == super_volume_serial
            ).first()
            if parent is None:
                raise SuperVolumeNotFoundError(super_volume_serial)

            rows = []
            missing = []
            for volume_id in volume_ids:
                row = session.query(SuperVolumeStructureModel).filter(
                    SuperVolumeStructureModel.super_volume_id == super_volume_serial,
                    SuperVolumeStructureModel.volume_id == volume_id,
                    SuperVolumeStructureModel.state == SuperVolumeRelationState.USING,
                ).first()
                if row is None:
                    missing.append(volume_id)
                else:
                    rows.append(row)
            if missing:
                raise ValueError(
                    f"卷 {'、'.join(missing)} 不是超级卷 {super_volume_serial} 的 USING 成员，无法移除"
                )
            for row in rows:
                row.state = SuperVolumeRelationState.UNUSED

    def remove_super_volume(self, serial: str) -> None:
        """
        将超级卷标记为 REMOVED（软删除），并释放其 USING 子卷关联。

        移除成功时，会把本超级卷名下的子卷关联行（super_volume_id == serial 且
        state == USING）一并置为 SUPER_VOLUME_REMOVED，释放这些子卷；否则父行软删后，
        子卷会因仍处于 USING 而被 `_ensure_sub_volume_available` 视为占用。
        用独立状态（而非 UNUSED）是为了与「成员移除」区分：只有本方法释放的关联行
        会被 `revive_super_volume` 恢复，不会把 `remove_volumes` 摘除的成员挂回来。

        Note:
            置为 REMOVED 只能走本方法，不要用 `update_super_volume(state=REMOVED)` ——
            仓储层会直接拒绝，那样会绕过上面的引用校验。
            被移除的超级卷可经 `revive_super_volume` 复活（state 置回 UNKNOWN，拓扑一并恢复）。

        Args:
            serial: 超级卷序列号

        Raises:
            SuperVolumeNotFoundError: 超级卷不存在
            SuperVolumeAlreadyRemovedError: 超级卷已处于 REMOVED（不可重复移除）
        """
        with session_scope(self.session_factory) as session:
            model = (
                session.query(SuperVolumeModel)
                .filter(SuperVolumeModel.serial == serial)
                .first()
            )
            if model is None:
                raise SuperVolumeNotFoundError(serial)
            if model.state == SuperVolumeState.REMOVED:
                raise SuperVolumeAlreadyRemovedError(serial)

            session.query(SuperVolumeStructureModel).filter(
                SuperVolumeStructureModel.super_volume_id == serial,
                SuperVolumeStructureModel.state == SuperVolumeRelationState.USING,
            ).update({"state": SuperVolumeRelationState.SUPER_VOLUME_REMOVED})
            model.state = SuperVolumeState.REMOVED
            session.commit()

    def revive_super_volume(self, serial: str) -> None:
        """
        复活已移除（REMOVED）的超级卷：原地把 state 置回 UNKNOWN。

        复活是可逆软删除的逆操作：行原地 UPDATE（serial 是主键，不能重新 INSERT），
        其余字段保持删除前的值不变。目标状态为 UNKNOWN（复活 ≠ 立即可用）。

        拓扑一并恢复：把 `remove_super_volume` 释放掉的那批子卷关联行
        （state == SUPER_VOLUME_REMOVED）重新置回 USING；
        `remove_volumes` 摘除的成员（state == UNUSED）**不**恢复。

        前置校验（任一失败均抛异常，事务整体回滚）：
        - 目标存在、且正处于 REMOVED；
        - 待恢复的每个子卷都未被他处占用且可用 → 透传 SubVolumeInUseError /
          SubVolumeUnavailableError / SubVolumeNotFoundError（与挂载同口径）。

        Args:
            serial: 超级卷序列号

        Raises:
            SuperVolumeNotFoundError: 超级卷不存在
            SuperVolumeNotRemovedError: 超级卷未处于 REMOVED（无需复活）
            SubVolumeInUseError: 待恢复的子卷已被其它超级卷占用
            SubVolumeUnavailableError: 待恢复的子卷已 REMOVED / FAULT
            SubVolumeNotFoundError: 待恢复的子卷不存在
        """
        with session_scope(self.session_factory) as session:
            model = (
                session.query(SuperVolumeModel)
                .filter(SuperVolumeModel.serial == serial)
                .first()
            )
            if model is None:
                raise SuperVolumeNotFoundError(serial)
            if model.state != SuperVolumeState.REMOVED:
                raise SuperVolumeNotRemovedError(serial, model.state)

            # 不校验自身是否被引用：被引用的超级卷进不了 REMOVED（remove_super_volume 用
            # AlreadyRemoved 防重复、且释放子卷），故「REMOVED 且仍被引用」属脏库情形，
            # 而复活正是其修复手段 —— 复活后 state 与引用关系重新自洽。
            # 恢复拓扑：把软删时释放的子卷（SUPER_VOLUME_REMOVED）逐项挂回 USING。
            # 每一项先做「未被他处占用 + 仍存在且可用（非 REMOVED/FAULT）」校验；
            # 任一不通过就抛异常，由 session_scope 整体回滚（state 与拓扑都不会被改动）。
            released_rows = (
                session.query(SuperVolumeStructureModel)
                .filter(
                    SuperVolumeStructureModel.super_volume_id == serial,
                    SuperVolumeStructureModel.state
                    == SuperVolumeRelationState.SUPER_VOLUME_REMOVED,
                )
                .all()
            )
            for row in released_rows:
                _ensure_sub_volume_available(session, row.volume_id)
                row.state = SuperVolumeRelationState.USING

            model.state = SuperVolumeState.UNKNOWN
            session.commit()
