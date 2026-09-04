# CHECK: 待检查 - 基础设施 Volume 仓储实现 - 卷数据持久化

import logging

from domain.storage.file.enum import FileState
from domain.storage.super_device.enum import RelationState
from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.errors import VolumeInUseError
from domain.storage.volume.repo import volume_repository_abc
from infra.persistence.database import session_scope
from infra.persistence.models import (
    DeviceModel,
    FileLocationsModel,
    SuperDeviceModel,
    SuperVolumeStructureModel,
    VolumeModel,
)

logger = logging.getLogger(__name__)


class VolumeRepository(volume_repository_abc):
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

        注册前会校验 device_id 是否为有效的 Device 或 SuperDevice。

        Args:
            volume: 要注册的卷对象

        Raises:
            ValueError: device_id 既不是有效 Device 也不是有效 SuperDevice
        """
        volume_model = VolumeModel(
            serial=volume.serial,
            device_id=volume.device_id,
            name=volume.name,
            add_time=volume.add_time,
            last_check_time=volume.last_check_time,
            state=volume.state,
            capacity=volume.capacity,
            unique_mount_point=volume.unique_mount_point
            if volume.unique_mount_point is not None
            else "None",
            file_system=volume.file_system,
            info=volume.info if volume.info is not None else "",
        )
        with session_scope(self.session_factory) as session:
            # 兜底校验：device_id 必须是存在的 Device 或 SuperDevice
            device_exists = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == volume.device_id)
                .first()
                is not None
            )
            super_device_exists = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == volume.device_id)
                .first()
                is not None
            )
            if not device_exists and not super_device_exists:
                raise ValueError(
                    f"device_id '{volume.device_id}' 既不是有效 Device，也不是有效 SuperDevice"
                )
            session.add(volume_model)
            session.commit()

    def get_volume(self, serial: str) -> Volume | None:
        """
        根据序列号获取卷。

        Args:
            serial: 卷的序列号

        Returns:
            卷对象，若不存在则返回 None
        """
        with session_scope(self.session_factory) as session:
            volume_model = session.query(VolumeModel).filter(
                VolumeModel.serial == serial
            ).first()
            if volume_model is None:
                return None
            return Volume.from_dict({
                "serial": volume_model.serial,
                "device_id": volume_model.device_id,
                "name": volume_model.name,
                "add_time": volume_model.add_time,
                "last_check_time": volume_model.last_check_time,
                "state": volume_model.state,
                "capacity": volume_model.capacity,
                "unique_mount_point": volume_model.unique_mount_point,
                "file_system": volume_model.file_system,
                "info": volume_model.info,
            })

    def list_volumes(self) -> list[Volume]:
        """
        获取所有已注册的卷列表。

        Returns:
            卷对象列表
        """
        with session_scope(self.session_factory) as session:
            volume_models = session.query(VolumeModel).all()
            return [
                Volume.from_dict({
                    "serial": volume_model.serial,
                    "device_id": volume_model.device_id,
                    "name": volume_model.name,
                    "add_time": volume_model.add_time,
                    "last_check_time": volume_model.last_check_time,
                    "state": volume_model.state,
                    "capacity": volume_model.capacity,
                    "unique_mount_point": volume_model.unique_mount_point,
                    "file_system": volume_model.file_system,
                    "info": volume_model.info,
                })
                for volume_model in volume_models
            ]

    def update_volume(self, serial: str, **fields) -> None:
        """
        更新卷的指定字段。

        Args:
            serial: 卷序列号
            **fields: 要更新的字段名和值

        Raises:
            ValueError: 卷不存在
        """
        with session_scope(self.session_factory) as session:
            volume_model = (
                session.query(VolumeModel)
                .filter(VolumeModel.serial == serial)
                .first()
            )
            if volume_model is None:
                raise ValueError(f"volume {serial} not found")
            for key, value in fields.items():
                setattr(volume_model, key, value)
            session.commit()

    def update_serial(self, old_serial: str, new_serial: str) -> None:
        """
        重置卷序列号，并同步更新关联表（file_locations、super_volume_structures）中的外键引用。

        Args:
            old_serial: 原序列号
            new_serial: 新序列号

        Raises:
            ValueError: 原序列号对应的卷不存在
        """
        with session_scope(self.session_factory) as session:
            # 更新卷自身主键
            row = (
                session.query(VolumeModel)
                .filter(VolumeModel.serial == old_serial)
                .first()
            )
            if row is None:
                raise ValueError(f"volume {old_serial} not found")
            session.delete(row)
            session.flush()

            row.serial = new_serial
            session.add(row)
            session.flush()

            # 更新 file_locations 中引用的 now_volume
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

            session.commit()

    def remove_volume(self, serial: str) -> None:
        """
        将卷标记为 REMOVED（软删除），保留记录与关联完整性。

        移除前检查卷是否仍被引用：
        - file_locations 中 now_volume == serial 且 state != REMOVED
        - super_volume_structures 中 volume_id == serial 且 state == USING
        存在任意引用则抛出 VolumeInUseError，不执行移除（事务回滚）。

        Args:
            serial: 卷序列号

        Raises:
            ValueError: 卷不存在
            VolumeInUseError: 卷仍被引用
        """
        with session_scope(self.session_factory) as session:
            volume_model = (
                session.query(VolumeModel)
                .filter(VolumeModel.serial == serial)
                .first()
            )
            if volume_model is None:
                raise ValueError(f"volume {serial} not found")

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
                    SuperVolumeStructureModel.state == RelationState.USING,
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
