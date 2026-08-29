# CHECK: 待检查 - 基础设施 SuperDevice 仓储实现 - 超级设备数据持久化

import logging
from typing import Any

from domain.storage.device.enum import DeviceState
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_device.errors import (
    SubDeviceInUseError,
    SubDeviceNotFoundError,
    SubDeviceUnavailableError,
    SuperDeviceInUseError,
)
from domain.storage.volume.enum import VolumeState
from domain.storage.super_device.repo import super_device_repository_abc
from infra.persistence.database import session_scope
from infra.persistence.models import (
    DeviceModel,
    RelationState,
    SuperDeviceModel,
    SuperDeviceStructureModel,
    VolumeModel,
)

logger = logging.getLogger(__name__)

# 子项实体处于这些状态时视为「不可用」，禁止作为超级设备的子项挂载
_UNAVAILABLE_DEVICE_STATES = {DeviceState.REMOVED, DeviceState.FAULT}
_UNAVAILABLE_SUPER_DEVICE_STATES = {SuperDeviceState.REMOVED, SuperDeviceState.FAULT}


def _parse_structure_info(info_str: str | None) -> dict:
    """
    解析 SuperDeviceStructureModel.info 中的 JSON 文本。

    Args:
        info_str: JSON 格式的字符串或 None

    Returns:
        解析后的字典，解析失败或输入为空时返回空字典
    """
    if not info_str:
        return {}
    import json
    try:
        return json.loads(info_str)
    except (json.JSONDecodeError, TypeError):
        return {}


def _resolve_sub(session, sub_id: str) -> tuple[str, Any] | None:
    """
    解析子项类型：是 device 还是 super_device（支持层叠）。

    Args:
        session: SQLAlchemy 会话
        sub_id: 子项序列号

    Returns:
        (kind, model) 元组；kind 为 "device" 或 "super_device"，查不到返回 None
    """
    device = (
        session.query(DeviceModel)
        .filter(DeviceModel.serial == sub_id)
        .first()
    )
    if device is not None:
        return "device", device
    super_device = (
        session.query(SuperDeviceModel)
        .filter(SuperDeviceModel.serial == sub_id)
        .first()
    )
    if super_device is not None:
        return "super_device", super_device
    return None


def _ensure_sub_available(session, sub_id: str) -> None:
    """
    校验子项可挂载：独占（未被其它超级设备以 USING 占用）+ 实体可用（非 REMOVED/FAULT）。

    Args:
        session: SQLAlchemy 会话
        sub_id: 子项序列号

    Raises:
        SubDeviceInUseError: 子项已被其它超级设备以 USING 占用
        SubDeviceNotFoundError: 子项既不是 device 也不是 super_device
        SubDeviceUnavailableError: 子项实体处于 REMOVED/FAULT 不可用状态
    """
    holder = (
        session.query(SuperDeviceStructureModel)
        .filter(
            SuperDeviceStructureModel.sub_device_id == sub_id,
            SuperDeviceStructureModel.state == RelationState.USING,
        )
        .first()
    )
    if holder is not None:
        raise SubDeviceInUseError(sub_id, holder.super_device_id)

    resolved = _resolve_sub(session, sub_id)
    if resolved is None:
        raise SubDeviceNotFoundError(sub_id)
    kind, model = resolved
    if kind == "device" and model.state in _UNAVAILABLE_DEVICE_STATES:
        raise SubDeviceUnavailableError(sub_id, model.state)
    if kind == "super_device" and model.state in _UNAVAILABLE_SUPER_DEVICE_STATES:
        raise SubDeviceUnavailableError(sub_id, model.state)


class SuperDeviceRepository(super_device_repository_abc):
    """超级设备仓库实现，提供超级设备数据的持久化存储和查询操作。"""

    def __init__(self, session_factory) -> None:
        """
        初始化 SuperDeviceRepository。

        Args:
            session_factory: 用于创建 SQLAlchemy 会话的工厂
        """
        self.session_factory = session_factory
        super().__init__()
        logger.info("SuperDeviceRepository constructed")
    def is_exist(self, super_device: SuperDevice | str) -> bool:
        """
        判断超级设备是否已存在于数据库中。

        Args:
            super_device: 超级设备对象或序列号字符串

        Returns:
            存在返回 True，否则返回 False
        """
        if isinstance(super_device, SuperDevice):
            serial = super_device.serial
        else:
            serial = super_device
        with session_scope(self.session_factory) as session:
            return session.query(SuperDeviceModel).filter(SuperDeviceModel.serial == serial).first() is not None
    def reg_super_device(self, super_device: SuperDevice) -> None:
        """
        注册一个新的超级设备及其子设备关联关系。

        超级设备主行与其所有子设备关联行在同一事务内提交，
        避免「超级设备已落库、关联行写入失败」产生的脏数据。

        Args:
            super_device: 要注册的超级设备对象
        """
        super_device_model = SuperDeviceModel(
            serial=super_device.serial,
            name=super_device.name,
            type=super_device.sdtype,
            need_all_devices_online=super_device.need_all_devices_online,
            add_time=super_device.add_time,
            last_check_time=super_device.last_check_time,
            state=super_device.state,
            capacity=super_device.capacity,
            info=super_device.info,
        )
        devices = []
        for device in super_device.devices:
            super_device_structure_model = SuperDeviceStructureModel(
                super_device_id=super_device.serial,
                sub_device_id=device,
                add_time=super_device.add_time,
                state=RelationState.USING,
                info=super_device.info,
            )
            devices.append(super_device_structure_model)
        # 超级设备主行 + 全部关联行：同一个事务，保证原子性（session_scope 退出时自动 commit）
        with session_scope(self.session_factory) as session:
            # 挂载前校验每个子项：独占（未被其它超级设备 USING 占用）+ 实体可用
            for sub_id in super_device.devices:
                _ensure_sub_available(session, sub_id)
            session.add(super_device_model)
            session.add_all(devices)

    @staticmethod
    def _model_to_dict(model: SuperDeviceModel, device_ids: list[str]) -> dict[str, Any]:
        """
        将 SuperDeviceModel 转换为字典。

        Args:
            model: SuperDeviceModel 实例
            device_ids: 子设备序列号列表

        Returns:
            包含所有字段的字典
        """
        return {
            "serial": model.serial,
            "name": model.name,
            "type": model.type,
            "need_all_devices_online": model.need_all_devices_online,
            "add_time": model.add_time,
            "last_check_time": model.last_check_time,
            "state": model.state,
            "capacity": model.capacity,
            "info": model.info,
            "devices": device_ids,
        }

    def get_super_device(self, super_device_serial: str) -> SuperDevice | None:
        """
        根据序列号获取超级设备。

        Args:
            super_device_serial: 超级设备序列号

        Returns:
            超级设备对象，若不存在则返回 None
        """
        with session_scope(self.session_factory) as session:
            model = session.query(SuperDeviceModel).filter(
                SuperDeviceModel.serial == super_device_serial
            ).first()
            if model is None:
                return None
            structure_rows = session.query(SuperDeviceStructureModel).filter(
                SuperDeviceStructureModel.super_device_id == super_device_serial,
                SuperDeviceStructureModel.state == RelationState.USING,
            ).all()
            device_ids = [row.sub_device_id for row in structure_rows]
            data = self._model_to_dict(model, device_ids)
            return SuperDevice.from_dict(data)


    def list_super_device(self) -> list[SuperDevice]:
        """
        获取所有已注册的超级设备列表。

        Returns:
            超级设备对象列表
        """
        with session_scope(self.session_factory) as session:
            models = session.query(SuperDeviceModel).all()
            result = []
            for model in models:
                structure_rows = session.query(SuperDeviceStructureModel).filter(
                    SuperDeviceStructureModel.super_device_id == model.serial,
                    SuperDeviceStructureModel.state == RelationState.USING,
                ).all()
                device_ids = [row.sub_device_id for row in structure_rows]
                data = self._model_to_dict(model, device_ids)
                result.append(SuperDevice.from_dict(data))
            return result

    # 领域字段名 → 模型列名 映射
    _field_mapping = {
        "sdtype": "type",
    }

    def update_super_device(self, serial: str, **fields) -> None:
        """
        更新超级设备的指定字段。

        Args:
            serial: 超级设备序列号
            **fields: 要更新的字段名和值（支持 sdtype 自动映射为 type）

        Raises:
            ValueError: 超级设备不存在
        """
        with session_scope(self.session_factory) as session:
            model = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == serial)
                .first()
            )
            if model is None:
                raise ValueError(f"super_device {serial} not found")
            for key, value in fields.items():
                col = self._field_mapping.get(key, key)
                setattr(model, col, value)
            session.commit()

    def update_super_device_serial(self, old_serial: str, new_serial: str) -> None:
        """
        重置超级设备序列号，同步更新关联表中的外键引用。

        super_devices.serial 是主键，被以下位置引用，需一并迁移：
        - super_device_structures.super_device_id（作为父时的子项关联，有 FK）
        - super_device_structures.sub_device_id（作为子项被层叠引用）
        - volumes.device_id（卷建立在超级设备上）

        因 super_device_structures.super_device_id 有外键指向 super_devices.serial，
        不能像 device 那样 delete→改主键→add（删除旧父行会被 FK 拦），
        改为「先以 new_serial 复制新主键行 → 迁移引用 → 再删旧行」。

        Args:
            old_serial: 原序列号
            new_serial: 新序列号

        Raises:
            ValueError: 原序列号对应的超级设备不存在
        """
        with session_scope(self.session_factory) as session:
            row = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == old_serial)
                .first()
            )
            if row is None:
                raise ValueError(f"super_device {old_serial} not found")

            # 1. 以 new_serial 复制主键行（先让新主键存在，FK 才能指向它）
            new_row = SuperDeviceModel(
                serial=new_serial,
                name=row.name,
                type=row.type,
                need_all_devices_online=row.need_all_devices_online,
                add_time=row.add_time,
                last_check_time=row.last_check_time,
                state=row.state,
                capacity=row.capacity,
                info=row.info,
            )
            session.add(new_row)
            session.flush()

            # 2. 迁移引用表：old → new
            session.query(SuperDeviceStructureModel).filter(
                SuperDeviceStructureModel.super_device_id == old_serial
            ).update({"super_device_id": new_serial})
            session.query(SuperDeviceStructureModel).filter(
                SuperDeviceStructureModel.sub_device_id == old_serial
            ).update({"sub_device_id": new_serial})
            session.query(VolumeModel).filter(
                VolumeModel.device_id == old_serial
            ).update({"device_id": new_serial})

            # 3. 删除旧主键行
            session.delete(row)
            session.commit()

    # ── 子设备管理 ────────────────────────────────────────────────

    def add_device(self, super_device_serial: str, device_serial: str, add_time) -> None:
        """
        向超级设备新增一个子设备。

        Args:
            super_device_serial: 超级设备序列号
            device_serial: 子设备序列号
            add_time: 添加时间
        """
        with session_scope(self.session_factory) as session:
            _ensure_sub_available(session, device_serial)
            row = SuperDeviceStructureModel(
                super_device_id=super_device_serial,
                sub_device_id=device_serial,
                add_time=add_time,
                state=RelationState.USING,
                info="",
            )
            session.add(row)
            session.commit()

    def replace_device(
        self, super_device_serial: str, old_device_serial: str,
        new_device_serial: str, add_time,
    ) -> None:
        """
        替换超级设备中的子设备（将旧设备标记为 UNUSED，添加新设备映射）。

        Args:
            super_device_serial: 超级设备序列号
            old_device_serial: 被替换的子设备序列号
            new_device_serial: 新子设备序列号
            add_time: 添加时间

        Raises:
            ValueError: 旧设备未在超级设备中找到
        """
        with session_scope(self.session_factory) as session:
            # 0. 校验新子项可挂载（独占 + 实体可用），fail-fast
            _ensure_sub_available(session, new_device_serial)
            # 1. 查找旧映射，标记 UNUSED
            old_row = (
                session.query(SuperDeviceStructureModel)
                .filter(
                    SuperDeviceStructureModel.super_device_id == super_device_serial,
                    SuperDeviceStructureModel.sub_device_id == old_device_serial,
                    SuperDeviceStructureModel.state == RelationState.USING,
                )
                .first()
            )
            if old_row is None:
                raise ValueError(
                    f"device {old_device_serial} not found in super_device {super_device_serial}"
                )
            old_row.state = RelationState.UNUSED

            # 2. 旧映射的 info 中记录 replaced_by
            old_info = _parse_structure_info(old_row.info)
            old_info["replaced_by"] = new_device_serial
            import json
            old_row.info = json.dumps(old_info, ensure_ascii=False)

            # 3. 新增新设备映射
            new_row = SuperDeviceStructureModel(
                super_device_id=super_device_serial,
                sub_device_id=new_device_serial,
                add_time=add_time,
                state=RelationState.USING,
                info="",
            )
            session.add(new_row)
            session.commit()

    def remove_device(self, super_device_serial: str, device_serial: str) -> None:
        """
        从超级设备移除一个子设备（将其状态标记为 UNUSED）。

        Args:
            super_device_serial: 超级设备序列号
            device_serial: 要移除的子设备序列号

        Raises:
            ValueError: 设备未在超级设备中找到
        """
        with session_scope(self.session_factory) as session:
            row = (
                session.query(SuperDeviceStructureModel)
                .filter(
                    SuperDeviceStructureModel.super_device_id == super_device_serial,
                    SuperDeviceStructureModel.sub_device_id == device_serial,
                    SuperDeviceStructureModel.state == RelationState.USING,
                )
                .first()
            )
            if row is None:
                raise ValueError(
                    f"device {device_serial} not found in super_device {super_device_serial}"
                )
            row.state = RelationState.UNUSED
            session.commit()

    def remove_super_device(self, serial: str) -> None:
        """
        将超级设备标记为 REMOVED（软删除），保留记录与关联完整性。

        移除前检查超级设备是否仍被引用：
        - super_device_structures 中 sub_device_id == serial 且 state == USING（被层叠）
        - volumes 中 device_id == serial 且 state != REMOVED（卷建立在超级设备上）
        存在任意引用则抛出 SuperDeviceInUseError，不执行移除（事务回滚）。

        Args:
            serial: 超级设备序列号

        Raises:
            ValueError: 超级设备不存在
            SuperDeviceInUseError: 超级设备仍被引用
        """
        with session_scope(self.session_factory) as session:
            model = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == serial)
                .first()
            )
            if model is None:
                raise ValueError(f"super_device {serial} not found")

            super_using = (
                session.query(SuperDeviceStructureModel)
                .filter(
                    SuperDeviceStructureModel.sub_device_id == serial,
                    SuperDeviceStructureModel.state == RelationState.USING,
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
                raise SuperDeviceInUseError(
                    serial,
                    super_device_using=super_using,
                    volumes=volumes,
                )

            model.state = SuperDeviceState.REMOVED
            session.commit()