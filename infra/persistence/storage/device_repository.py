import logging
from typing import Any

from sqlalchemy.orm import make_transient

from domain.storage.device.base import Device
from domain.storage.device.enum import DeviceState
from domain.storage.device.errors import (
    DeviceAlreadyRegisteredError,
    DeviceAlreadyRemovedError,
    DeviceInUseError,
    DeviceNotFoundError,
    DeviceNotRemovedError,
)
from domain.storage.device.repo import DeviceRepositoryABC
from domain.storage.super_device.enum import SuperDeviceRelationState
from infra.persistence._enum_utils import coerce_enum
from infra.persistence._model_utils import updatable_fields
from infra.persistence.database import session_scope
from infra.persistence.models import (
    DeviceModel,
    SuperDeviceStructureModel,
    VolumeModel,
    VolumeState,
)

logger = logging.getLogger(__name__)


class DeviceRepository(DeviceRepositoryABC):
    """设备仓库实现，提供设备数据的持久化存储和查询操作。"""

    def __init__(self, session_factory) -> None:
        """
        初始化 device_repository。

        Args:
            session_factory: 用于创建 SQLAlchemy 会话的工厂
        """
        self.session_factory = session_factory
        super().__init__()
        logger.info("DeviceRepository constructed")

    def is_exist(self, device: Device | str) -> bool:
        """
        判断设备是否已存在于数据库中。

        Args:
            device: 设备对象或设备序列号字符串

        Returns:
            存在返回 True，否则返回 False
        """
        if isinstance(device, Device):
            serial = device.serial
        else:
            serial = device
        with session_scope(self.session_factory) as session:
            return session.query(DeviceModel).filter(DeviceModel.serial == serial).first() is not None

    def reg_device(self, device: Device) -> None:
        """
        注册一个新设备到数据库。

        Args:
            device: 要注册的设备对象

        Raises:
            DeviceAlreadyRegisteredError: 该 serial 已被一条非 REMOVED 的行占用
            DeviceAlreadyRemovedError: 该 serial 被一条 REMOVED（软删除）行占位，需先复活
        """
        # 这里需要用device初始化一个DeviceModel
        device_model = DeviceModel(
                serial=device.serial,
                name=device.name,
                dtype=device.dtype,
                add_time=device.add_time,
                last_check_time=device.last_check_time,
                state=coerce_enum(DeviceState, device.state),
                capacity=device.capacity,
                info=device.info,
            )
        with session_scope(self.session_factory) as session:
            # 唯一性预检：serial 是主键，任何已存在的行（含 REMOVED）都算占用。
            # 在这里判定（而不是让 INSERT 撞 PK），使调用方——含绕过 service 的——都能拿到
            # 结构化领域异常而非裸 IntegrityError。
            # 注：预检不替代 DB 约束（并发 TOCTOU 仍可能撞 PK），那条路径仍由 DB 兜底。
            existing = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == device.serial)
                .first()
            )
            if existing is not None:
                # 分类就在仓储完成：REMOVED 行占位 与 活跃占用 是互斥的两种事实，
                # 各给一个异常类型，上层不必再自己看 state 分流。
                if existing.state == DeviceState.REMOVED:
                    raise DeviceAlreadyRemovedError(device.serial)
                raise DeviceAlreadyRegisteredError(device.serial, state=existing.state)
            session.add(device_model)
            session.commit()
            
    @staticmethod
    def _model_to_dict(model: DeviceModel) -> dict[str, Any]:
        """
        将 DeviceModel 转换为字典（供 Device.from_dict 使用）。

        get_device / list_devices 共用同一份字段清单，避免两处重复维护。

        Args:
            model: DeviceModel 实例

        Returns:
            包含所有字段的字典
        """
        return {
            "serial": model.serial,
            "name": model.name,
            "dtype": model.dtype,
            "add_time": model.add_time,
            "last_check_time": model.last_check_time,
            "state": model.state,
            "capacity": model.capacity,
            "info": model.info,
        }

    def get_device(self, serial: str, exclude_removed: bool = True) -> Device | None:
        """
        根据序列号获取设备。

        Args:
            serial: 设备序列号
            exclude_removed: 为 True（默认）时，已移除（REMOVED）的设备视为不存在

        Returns:
            设备对象，若不存在则返回 None
        """
        with session_scope(self.session_factory) as session:
            query = session.query(DeviceModel).filter(DeviceModel.serial == serial)
            if exclude_removed:
                query = query.filter(DeviceModel.state != DeviceState.REMOVED)
            device_model = query.first()
            if device_model is None:
                return None
            return Device.from_dict(self._model_to_dict(device_model))

    def list_devices(self, exclude_removed: bool = True) -> list[Device]:
        """
        获取已注册设备的列表。

        Args:
            exclude_removed: 为 True（默认）时排除已移除（REMOVED）的设备。

        Returns:
            设备对象列表
        """
        with session_scope(self.session_factory) as session:
            query = session.query(DeviceModel)
            if exclude_removed:
                query = query.filter(DeviceModel.state != DeviceState.REMOVED)
            device_models = query.all()
            return [
                Device.from_dict(self._model_to_dict(device_model))
                for device_model in device_models
            ]

    def update_device(self, serial: str, /, **fields) -> None:
        """
        更新设备的指定字段。

        值为 None 的字段视为「未提供」，保持原值不变（区别于「清空」）。
        可更新字段自动取自 DeviceModel 的列（主键 serial 除外），未知字段会报错，
        避免拼错键名时静默无效。

        Note:
            `serial` 是位置参数（positional-only），不能作为关键字传入；序列号不可经本方法
            修改（会直接报错），改名请走 `update_serial`（会同步迁移关联表引用）。

        Args:
            serial: 设备序列号（位置参数）
            **fields: 要更新的字段名和值；None 表示不修改该字段

        Raises:
            DeviceNotFoundError: 设备不存在
            ValueError: 含未知字段；或试图修改 serial（须走 update_serial）；
                或把 state 改为 REMOVED（软删除必须走 remove_device，以免绕过引用校验）
        """
        with session_scope(self.session_factory) as session:
            device_model = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == serial)
                .first()
            )
            if device_model is None:
                raise DeviceNotFoundError(serial)
            allowed = updatable_fields(DeviceModel)
            for key, value in fields.items():
                if key == "serial":
                    # 改名必须走 update_serial：它会同步迁移 volumes.device_id /
                    # super_device_structures.sub_device_id 等关联引用，通用通道不会。
                    raise ValueError(
                        f"device {serial} 不允许通过 update_device 修改序列号，"
                        f"请改用 update_serial（会同步迁移关联表引用）"
                    )
                if key not in allowed:
                    raise ValueError(
                        f"device {serial} 不支持更新字段 {key!r}；"
                        f"可更新字段：{', '.join(sorted(allowed))}"
                    )
                if value is None:  # None = 未提供该字段 → 保持原样
                    continue
                if key == "state":
                    value = coerce_enum(DeviceState, value)
                    if value is DeviceState.REMOVED:
                        raise ValueError(
                            f"device {serial} 不允许通过 update_device 置为 REMOVED，"
                            f"请改用 remove_device（带引用校验）"
                        )
                setattr(device_model, key, value)
            session.commit()

    def update_serial(self, old_serial: str, new_serial: str) -> None:
        """
        重置设备序列号，并同步更新关联表（volumes、super_device_structures）中的外键引用。

        Args:
            old_serial: 原序列号
            new_serial: 新序列号

        Raises:
            DeviceNotFoundError: 原序列号对应的设备不存在
            DeviceAlreadyRemovedError: 新序列号被一条 REMOVED（软删除）行占位
            DeviceAlreadyRegisteredError: 新序列号已被一条非 REMOVED 的行占用
        """
        with session_scope(self.session_factory) as session:
            # 更新设备自身主键
            row = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == old_serial)
                .first()
            )
            if row is None:
                raise DeviceNotFoundError(old_serial)
            if old_serial == new_serial:
                return

            # 预检：目标 serial 是否已被占用。serial 是主键，任何已存在的行（含 REMOVED 墓碑）
            # 都算占用；不预检的话，下面的 delete→改主键→add 会在 flush 时撞 PK 抛裸
            # IntegrityError。分类与 reg_device 同口径：墓碑 → AlreadyRemoved，活跃 → AlreadyRegistered。
            conflict = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == new_serial)
                .first()
            )
            if conflict is not None:
                if conflict.state == DeviceState.REMOVED:
                    raise DeviceAlreadyRemovedError(new_serial)
                raise DeviceAlreadyRegisteredError(new_serial, state=conflict.state)

            session.delete(row)
            session.flush()

            # delete + flush 后对象处于 deleted 状态，必须先用 make_transient
            # 把它变回“未保存的新对象”，才能改主键并重新 add
            make_transient(row)
            row.serial = new_serial
            session.add(row)
            session.flush()

            # 更新 volumes 中引用的 device_id
            (
                session.query(VolumeModel)
                .filter(VolumeModel.device_id == old_serial)
                .update({"device_id": new_serial})
            )

            # 更新 super_device_structures 中引用的 sub_device_id
            (
                session.query(SuperDeviceStructureModel)
                .filter(SuperDeviceStructureModel.sub_device_id == old_serial)
                .update({"sub_device_id": new_serial})
            )

            session.commit()

    def remove_device(self, serial: str) -> None:
        """
        将设备标记为 REMOVED（软删除），保留记录与关联完整性。

        移除前检查设备是否仍被引用：
        - super_device_structures 中 sub_device_id == serial 且 state == USING
        - volumes 中 device_id == serial 且 state != REMOVED
        存在任意引用则抛出 DeviceInUseError，不执行移除（事务回滚）。

        Note:
            置为 REMOVED 只能走本方法，不要用 `update_device(state=REMOVED)` ——
            仓储层会直接拒绝，那样会绕过上面的引用校验。
            被移除的设备可经 `revive_device` 复活（state 置回 UNKNOWN）。

        Args:
            serial: 设备序列号

        Raises:
            DeviceNotFoundError: 设备不存在
            DeviceAlreadyRemovedError: 设备已处于 REMOVED（不可重复移除）
            DeviceInUseError: 设备仍被引用
        """
        with session_scope(self.session_factory) as session:
            device_model = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == serial)
                .first()
            )
            if device_model is None:
                raise DeviceNotFoundError(serial)
            if device_model.state == DeviceState.REMOVED:
                raise DeviceAlreadyRemovedError(serial)

            super_using = (
                session.query(SuperDeviceStructureModel)
                .filter(
                    SuperDeviceStructureModel.sub_device_id == serial,
                    SuperDeviceStructureModel.state == SuperDeviceRelationState.USING,
                )
                .count()
            )
            volumes = (
                session.query(VolumeModel)
                .filter(
                    VolumeModel.device_id == serial,
                    VolumeModel.state != VolumeState.REMOVED,
                )
                .count()
            )
            if super_using or volumes:
                raise DeviceInUseError(
                    serial,
                    super_device_using=super_using,
                    volumes=volumes,
                )

            device_model.state = DeviceState.REMOVED
            session.commit()

    def revive_device(self, serial: str) -> None:
        """
        复活已移除（REMOVED）的设备：原地把 state 置回 UNKNOWN。

        复活是可逆软删除的逆操作：行原地 UPDATE（serial 是主键，不能重新 INSERT），
        其余字段保持删除前的值不变。目标状态为 UNKNOWN（复活 ≠ 立即可用）。

        只校验目标存在且正处于 REMOVED。**不校验是否被引用**：被引用的设备进不了
        REMOVED（`remove_device` 用 DeviceInUseError 把关），故那是脏库情形，
        而复活正是它的修复手段 —— 复活后 state 与引用关系重新自洽。

        Args:
            serial: 设备序列号

        Raises:
            DeviceNotFoundError: 设备不存在
            DeviceNotRemovedError: 设备未处于 REMOVED（无需复活）
        """
        with session_scope(self.session_factory) as session:
            device_model = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == serial)
                .first()
            )
            if device_model is None:
                raise DeviceNotFoundError(serial)
            if device_model.state != DeviceState.REMOVED:
                raise DeviceNotRemovedError(serial, device_model.state)

            # 不校验占用（曾抛 DeviceReviveBlockedError）：被引用的设备根本进不了 REMOVED，
            # 所以「REMOVED 且仍被 sd / volume 引用」只可能来自并发或手工改库，
            # 而这类脏状态恰恰该由复活修复（state 回到 UNKNOWN 后与引用关系自洽），
            # 拦下来只会把它永久卡死。
            # TODO(P1): 并发仍可能出错 —— remove_device 校验通过后、置 REMOVED 之前，
            #   该设备被别人挂为子项 / 建上卷，此时复活会照常成功（库内出现
            #   「非 REMOVED 且被引用」的常规态）。要堵这个窗口应在 remove_device 侧
            #   收口（加锁 / 落库前复检），而不是让 revive 拒绝修复。
            device_model.state = DeviceState.UNKNOWN
            session.commit()
