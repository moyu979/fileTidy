# CHECK: ai生成，待检查 - 基础设施 Device 仓储实现 - 设备数据持久化

import logging

from domain.storage.device.base import Device
from domain.storage.device.enum import DeviceState
from domain.storage.device.errors import DeviceInUseError
from domain.storage.device.repo import device_repository_abc
from infra.persistence.database import session_scope
from infra.persistence.models import (
    DeviceModel,
    RelationState,
    SuperDeviceStructureModel,
    VolumeModel,
    VolumeState,
)

logger = logging.getLogger(__name__)


class DeviceRepository(device_repository_abc):
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
        """
        # 这里需要用device初始化一个DeviceModel
        device_model = DeviceModel(
                serial=device.serial,
                name=device.name,
                type=device.dtype,
                add_time=device.add_time,
                last_check_time=device.last_check_time,
                capacity=device.capacity,
                info=device.info,
                state=device.state,
            )
        with session_scope(self.session_factory) as session:
            session.add(device_model)
            session.commit()
            
    def get_device(self, serial: str) -> Device | None:
        """
        根据序列号获取设备。

        Args:
            serial: 设备序列号

        Returns:
            设备对象，若不存在则返回 None
        """
        with session_scope(self.session_factory) as session:
            device_model = session.query(DeviceModel).filter(DeviceModel.serial == serial).first()
            if device_model is None:
                return None
            return Device.from_dict({
                "serial": device_model.serial,
                "name": device_model.name,
                "type": device_model.type,
                "add_time": device_model.add_time,
                "last_check_time": device_model.last_check_time,
                "capacity": device_model.capacity,
                "info": device_model.info,
                "state": device_model.state,
            })

    def list_devices(self) -> list[Device]:
        """
        获取所有已注册设备的列表。

        Returns:
            设备对象列表
        """
        with session_scope(self.session_factory) as session:
            device_models = session.query(DeviceModel).all()
            return [
                Device.from_dict({
                    "serial": device_model.serial,
                    "name": device_model.name,
                    "type": device_model.type,
                    "add_time": device_model.add_time,
                    "last_check_time": device_model.last_check_time,
                    "capacity": device_model.capacity,
                    "info": device_model.info,
                    "state": device_model.state,
                })
                for device_model in device_models
            ]

    def update_device(self, serial: str, **fields) -> None:
        """
        更新设备的指定字段。

        Args:
            serial: 设备序列号
            **fields: 要更新的字段名和值

        Raises:
            ValueError: 设备不存在
        """
        with session_scope(self.session_factory) as session:
            device_model = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == serial)
                .first()
            )
            if device_model is None:
                raise ValueError(f"device {serial} not found")
            for key, value in fields.items():
                setattr(device_model, key, value)
            session.commit()

    def update_serial(self, old_serial: str, new_serial: str) -> None:
        """
        重置设备序列号，并同步更新关联表（volumes、super_device_structures）中的外键引用。

        Args:
            old_serial: 原序列号
            new_serial: 新序列号

        Raises:
            ValueError: 原序列号对应的设备不存在
        """
        with session_scope(self.session_factory) as session:
            # 更新设备自身主键
            row = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == old_serial)
                .first()
            )
            if row is None:
                raise ValueError(f"device {old_serial} not found")
            session.delete(row)
            session.flush()

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

        Args:
            serial: 设备序列号

        Raises:
            ValueError: 设备不存在
            DeviceInUseError: 设备仍被引用
        """
        with session_scope(self.session_factory) as session:
            device_model = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == serial)
                .first()
            )
            if device_model is None:
                raise ValueError(f"device {serial} not found")

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
                raise DeviceInUseError(
                    serial,
                    super_device_using=super_using,
                    volumes=volumes,
                )

            device_model.state = DeviceState.REMOVED
            session.commit()
