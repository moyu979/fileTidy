import logging
from typing import Any

from domain.storage.device.enum import UNAVAILABLE_DEVICE_STATES
from domain.storage.file.enum import FileState
from domain.storage.super_device.enum import UNAVAILABLE_SUPER_DEVICE_STATES
from domain.storage.super_volume.enum import SuperVolumeRelationState
from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.errors import (
    VolumeAlreadyRegisteredError,
    VolumeAlreadyRemovedError,
    VolumeInUseError,
    VolumeNotFoundError,
    VolumeNotRemovedError,
)
from domain.storage.volume.repo import VolumeRepositoryABC
from infra.persistence._enum_utils import coerce_enum
from infra.persistence._model_utils import updatable_fields
from infra.persistence.database import session_scope
from infra.persistence.models import (
    DeviceModel,
    FileLocationsModel,
    SuperDeviceModel,
    SuperVolumeStructureModel,
    VolumeModel,
)

logger = logging.getLogger(__name__)


def _ensure_device_available(session, device_id: str) -> None:
    """校验 device_id 指向存在且可用的 Device 或 SuperDevice。

    这是卷挂载对象的统一把关口：既回答「是不是有效设备」，也回答
    「设备是否还可用」（REMOVED / FAULT 不可用）。

    Args:
        session: SQLAlchemy 会话
        device_id: 待校验的设备 / 超级设备序列号

    Raises:
        ValueError: 序列号既不是 Device 也不是 SuperDevice，
            或对应的实体处于 REMOVED / FAULT 不可用状态
    """
    device = (
        session.query(DeviceModel)
        .filter(DeviceModel.serial == device_id)
        .first()
    )
    if device is not None:
        if device.state in UNAVAILABLE_DEVICE_STATES:
            raise ValueError(
                f"device_id '{device_id}' 处于不可用状态 {device.state.name}，"
                f"不能作为卷的挂载对象"
            )
        return

    super_device = (
        session.query(SuperDeviceModel)
        .filter(SuperDeviceModel.serial == device_id)
        .first()
    )
    if super_device is not None:
        if super_device.state in UNAVAILABLE_SUPER_DEVICE_STATES:
            raise ValueError(
                f"device_id '{device_id}' 处于不可用状态 {super_device.state.name}，"
                f"不能作为卷的挂载对象"
            )
        return

    raise ValueError(
        f"device_id '{device_id}' 既不是有效 Device，也不是有效 SuperDevice"
    )


class VolumeRepository(VolumeRepositoryABC):
    """卷仓库实现，提供卷数据的持久化存储和查询操作。"""

    def __init__(self, session_factory) -> None:
        """
        初始化 VolumeRepository。

        Args:
            session_factory: 用于创建 SQLAlchemy 会话的工厂
        """
        self.session_factory = session_factory
        super().__init__()
        logger.info("VolumeRepository constructed")

    def is_exist(self, volume: Volume | str) -> bool:
        """
        判断卷是否已存在于数据库中。

        Args:
            volume: 卷对象或卷序列号字符串

        Returns:
            存在返回 True，否则返回 False
        """
        if isinstance(volume, Volume):
            serial = volume.serial
        else:
            serial = volume
        with session_scope(self.session_factory) as session:
            return session.query(VolumeModel).filter(VolumeModel.serial == serial).first() is not None

    def reg_volume(self, volume: Volume) -> None:
        """
        注册一个新的卷到数据库。

        注册前会校验 device_id 是否为有效且可用的 Device 或 SuperDevice。

        Args:
            volume: 要注册的卷对象

        Raises:
            VolumeAlreadyRegisteredError: 该 serial 已被一条非 REMOVED 的行占用
            VolumeAlreadyRemovedError: 该 serial 被一条 REMOVED（软删除）行占位，需先复活
            ValueError: device_id 既不是有效 Device 也不是有效 SuperDevice，
                或对应的实体处于 REMOVED / FAULT 不可用状态
        """
        volume_model = VolumeModel(
            serial=volume.serial,
            device_id=volume.device_id,
            name=volume.name,
            add_time=volume.add_time,
            last_check_time=volume.last_check_time,
            state=coerce_enum(VolumeState, volume.state),
            capacity=volume.capacity,
            unique_mount_point=volume.unique_mount_point,
            file_system=volume.file_system,
            info=volume.info,
        )
        with session_scope(self.session_factory) as session:
            # 唯一性预检：serial 是主键，任何已存在的行（含 REMOVED）都算占用。
            # 在这里判定（而不是让 INSERT 撞 PK），使调用方——含绕过 service 的——都能拿到
            # 结构化领域异常而非裸 IntegrityError。
            # 注：预检不替代 DB 约束（并发 TOCTOU 仍可能撞 PK），那条路径仍由 DB 兜底。
            existing = (
                session.query(VolumeModel)
                .filter(VolumeModel.serial == volume.serial)
                .first()
            )
            if existing is not None:
                # 分类就在仓储完成：REMOVED 行占位 与 活跃占用 是互斥的两种事实，
                # 各给一个异常类型，上层不必再自己看 state 分流。
                if existing.state == VolumeState.REMOVED:
                    raise VolumeAlreadyRemovedError(volume.serial)
                raise VolumeAlreadyRegisteredError(volume.serial, state=existing.state)
            # 兜底校验：device_id 必须是存在且可用的 Device 或 SuperDevice
            _ensure_device_available(session, volume.device_id)
            session.add(volume_model)
            session.commit()

    @staticmethod
    def _model_to_dict(model: VolumeModel) -> dict[str, Any]:
        """
        将 VolumeModel 转换为字典（供 Volume.from_dict 使用）。

        get_volume / list_volumes 共用同一份字段清单，避免两处重复维护。

        Args:
            model: VolumeModel 实例

        Returns:
            包含所有字段的字典
        """
        return {
            "serial": model.serial,
            "device_id": model.device_id,
            "name": model.name,
            "add_time": model.add_time,
            "last_check_time": model.last_check_time,
            "state": model.state,
            "capacity": model.capacity,
            "unique_mount_point": model.unique_mount_point,
            "file_system": model.file_system,
            "info": model.info,
        }

    def get_volume(self, serial: str, exclude_removed: bool = True) -> Volume | None:
        """
        根据序列号获取卷。

        Args:
            serial: 卷的序列号
            exclude_removed: 为 True（默认）时，已移除（REMOVED）的卷视为不存在

        Returns:
            卷对象，若不存在则返回 None
        """
        with session_scope(self.session_factory) as session:
            query = session.query(VolumeModel).filter(VolumeModel.serial == serial)
            if exclude_removed:
                query = query.filter(VolumeModel.state != VolumeState.REMOVED)
            volume_model = query.first()
            if volume_model is None:
                return None
            return Volume.from_dict(self._model_to_dict(volume_model))

    def list_volumes(self, exclude_removed: bool = True) -> list[Volume]:
        """
        获取已注册的卷列表。

        Args:
            exclude_removed: 为 True（默认）时排除已移除（REMOVED）的卷。

        Returns:
            卷对象列表
        """
        with session_scope(self.session_factory) as session:
            query = session.query(VolumeModel)
            if exclude_removed:
                query = query.filter(VolumeModel.state != VolumeState.REMOVED)
            volume_models = query.all()
            return [
                Volume.from_dict(self._model_to_dict(volume_model))
                for volume_model in volume_models
            ]

    def update_volume(self, serial: str, /, **fields) -> None:
        """
        更新卷的指定字段。

        值为 None 的字段视为「未提供」，保持原值不变（区别于「清空」）。
        可更新字段自动取自 VolumeModel 的列（主键 serial 除外），未知字段会报错，
        避免拼错键名时静默无效。

        更新 device_id 时会校验目标是否存在且可用（REMOVED / FAULT 不可用），
        口径与 reg_volume 一致。

        Note:
            `serial` 是位置参数（positional-only），不能作为关键字传入；序列号不可经本方法
            修改（会直接报错），改名请走 `update_serial`（会同步迁移关联表引用）。

        Args:
            serial: 卷序列号（位置参数）
            **fields: 要更新的字段名和值；None 表示不修改该字段

        Raises:
            VolumeNotFoundError: 卷不存在
            ValueError: 含未知字段；或试图修改 serial（须走 update_serial）；
                或把 state 改为 REMOVED（软删除必须走 remove_volume，以免绕过引用校验）；
                或 device_id 无效 / 不可用
        """
        with session_scope(self.session_factory) as session:
            volume_model = (
                session.query(VolumeModel)
                .filter(VolumeModel.serial == serial)
                .first()
            )
            if volume_model is None:
                raise VolumeNotFoundError(serial)
            allowed = updatable_fields(VolumeModel)
            for key, value in fields.items():
                if key == "serial":
                    # 改名必须走 update_serial：它会同步迁移 file_locations.now_volume /
                    # super_volume_structures.volume_id 等关联引用，通用通道不会。
                    raise ValueError(
                        f"volume {serial} 不允许通过 update_volume 修改序列号，"
                        f"请改用 update_serial（会同步迁移关联表引用）"
                    )
                if key not in allowed:
                    raise ValueError(
                        f"volume {serial} 不支持更新字段 {key!r}；"
                        f"可更新字段：{', '.join(sorted(allowed))}"
                    )
                if value is None:  # None = 未提供该字段 → 保持原样
                    continue
                if key == "state":
                    value = coerce_enum(VolumeState, value)
                    if value is VolumeState.REMOVED:
                        raise ValueError(
                            f"volume {serial} 不允许通过 update_volume 置为 REMOVED，"
                            f"请改用 remove_volume（带引用校验）"
                        )
                elif key == "device_id":
                    _ensure_device_available(session, value)
                setattr(volume_model, key, value)
            session.commit()

    def update_serial(self, old_serial: str, new_serial: str) -> None:
        """
        重置卷序列号，并同步更新关联表（file_locations、super_volume_structures）中的外键引用。

        Args:
            old_serial: 原序列号
            new_serial: 新序列号

        Raises:
            VolumeNotFoundError: 原序列号对应的卷不存在
            VolumeAlreadyRemovedError: 新序列号被一条 REMOVED（软删除）行占位
            VolumeAlreadyRegisteredError: 新序列号已被一条非 REMOVED 的行占用
        """
        with session_scope(self.session_factory) as session:
            # 更新卷自身主键
            row = (
                session.query(VolumeModel)
                .filter(VolumeModel.serial == old_serial)
                .first()
            )
            if row is None:
                raise VolumeNotFoundError(old_serial)
            if old_serial == new_serial:
                return

            # 预检：目标 serial 是否已被占用。serial 是主键，任何已存在的行（含 REMOVED 墓碑）
            # 都算占用；不预检的话，下面复制新主键行会在 flush 时撞 PK 抛裸 IntegrityError。
            # 分类与 reg_volume 同口径：墓碑 → AlreadyRemoved，活跃 → AlreadyRegistered。
            conflict = (
                session.query(VolumeModel)
                .filter(VolumeModel.serial == new_serial)
                .first()
            )
            if conflict is not None:
                if conflict.state == VolumeState.REMOVED:
                    raise VolumeAlreadyRemovedError(new_serial)
                raise VolumeAlreadyRegisteredError(new_serial, state=conflict.state)

            # volumes.serial 被 file_locations / super_volume_structures 外键引用，
            # 不能“先删旧行再迁移子引用”。改为与 SuperDeviceRepository 一致的
            # 顺序：先复制新主键行 → 迁移子表引用 → 再删旧行。
            new_row = VolumeModel(
                serial=new_serial,
                device_id=row.device_id,
                name=row.name,
                add_time=row.add_time,
                last_check_time=row.last_check_time,
                state=row.state,
                capacity=row.capacity,
                unique_mount_point=row.unique_mount_point,
                file_system=row.file_system,
                info=row.info,
            )
            session.add(new_row)
            session.flush()

            # 更新文件子系统对应的映射
            (
                session.query(FileLocationsModel)
                .filter(FileLocationsModel.now_volume == old_serial)
                .update({"now_volume": new_serial})
            )

            # 更新 super_volume_structures 中引用的 volume_id
            (
                session.query(SuperVolumeStructureModel)
                .filter(SuperVolumeStructureModel.volume_id == old_serial)
                .update({"volume_id": new_serial})
            )

            # 最后删除旧主键行
            session.delete(row)
            session.commit()

    def remove_volume(self, serial: str) -> None:
        """
        将卷标记为 REMOVED（软删除），保留记录与关联完整性。

        移除前检查卷是否仍被引用：
        - file_locations 中 now_volume == serial 且 state != REMOVED
        - super_volume_structures 中 volume_id == serial 且 state == USING
        存在任意引用则抛出 VolumeInUseError，不执行移除（事务回滚）。

        Note:
            置为 REMOVED 只能走本方法，不要用 `update_volume(state=REMOVED)` ——
            仓储层会直接拒绝，那样会绕过上面的引用校验。
            被移除的卷可经 `revive_volume` 复活（state 置回 UNKNOWN）。

        Args:
            serial: 卷序列号

        Raises:
            VolumeNotFoundError: 卷不存在
            VolumeAlreadyRemovedError: 卷已处于 REMOVED（不可重复移除）
            VolumeInUseError: 卷仍被引用
        """
        with session_scope(self.session_factory) as session:
            volume_model = (
                session.query(VolumeModel)
                .filter(VolumeModel.serial == serial)
                .first()
            )
            if volume_model is None:
                raise VolumeNotFoundError(serial)
            if volume_model.state == VolumeState.REMOVED:
                raise VolumeAlreadyRemovedError(serial)

            # 检查文件子系统约束
            files = (
                session.query(FileLocationsModel)
                .filter(
                    FileLocationsModel.now_volume == serial,
                    FileLocationsModel.state != FileState.REMOVED,
                )
                .count()
            )
            super_volumes = (
                session.query(SuperVolumeStructureModel)
                .filter(
                    SuperVolumeStructureModel.volume_id == serial,
                    SuperVolumeStructureModel.state == SuperVolumeRelationState.USING,
                )
                .count()
            )
            if files or super_volumes:
                raise VolumeInUseError(
                    serial,
                    super_volumes=super_volumes,
                    files=files,
                )

            volume_model.state = VolumeState.REMOVED
            session.commit()

    def revive_volume(self, serial: str) -> None:
        """
        复活已移除（REMOVED）的卷：原地把 state 置回 UNKNOWN。

        复活是可逆软删除的逆操作：行原地 UPDATE（serial 是主键，不能重新 INSERT），
        其余字段保持删除前的值不变。目标状态为 UNKNOWN（复活 ≠ 立即可用）。

        只校验目标存在、正处于 REMOVED，且挂载对象（`device_id` 指向的 Device 或
        SuperDevice）仍存在且可用。**不校验卷自身是否被引用**：被引用的卷进不了
        REMOVED（`remove_volume` 用 VolumeInUseError 把关），故那是脏库情形，
        而复活正是它的修复手段 —— 复活后 state 与引用关系重新自洽。

        Args:
            serial: 卷序列号

        Raises:
            VolumeNotFoundError: 卷不存在
            VolumeNotRemovedError: 卷未处于 REMOVED（无需复活）
            ValueError: 挂载对象（Device / SuperDevice）不存在或不可用
        """
        with session_scope(self.session_factory) as session:
            volume_model = (
                session.query(VolumeModel)
                .filter(VolumeModel.serial == serial)
                .first()
            )
            if volume_model is None:
                raise VolumeNotFoundError(serial)
            if volume_model.state != VolumeState.REMOVED:
                raise VolumeNotRemovedError(serial, volume_model.state)

            # 卷从 REMOVED 回到可用态前，必须确认挂载对象仍然有效：
            # 卷被软删后不再阻塞其 device / super_device 的移除（remove_device 只看
            # state != REMOVED 的卷），因此挂载对象可能已被 REMOVED；此时复活会造出
            # 「卷可用但挂在已移除对象上」的悬空状态，故在此拦截（口径同 reg / update）。
            _ensure_device_available(session, volume_model.device_id)

            volume_model.state = VolumeState.UNKNOWN
            session.commit()
