"""
设备服务 —— 去掉 DeviceSystemPort 依赖，直接调用系统函数。
保留类结构和 repository 注入，仓库保持原样。
"""

import json
from datetime import datetime
import logging
import os

from application.storage.device.factory import device_factory
from infra.system.storage.device.get_serial import get_serial
from infra.system.storage.device.get_type import get_type
from infra.system.storage.device.get_capacity import get_capacity
from infra.system.storage.device.get_healthy import get_healthy
from infra.system.path_manager.is_path import is_path
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN
from domain.storage.device.enum import DeviceState
from domain.storage.device.events import (
    DeviceFieldUpdated,
    DeviceInfoAppended,
    DeviceInfoKeyDeleted,
    DeviceInfoSet,
    DeviceRegistered,
    DeviceSerialChanged,
)
from infra.operate_log.operate_log import log_event

logger = logging.getLogger(__name__)


class device_service:
    def __init__(self, device_repository) -> None:
        self.device_repository = device_repository
        logger.info("Device service initialized")

    def reg_device_by_path(
        self,
        device_path: str,
        name: str | None,
        info: str | None,
    ) -> str:
        device_path = os.path.abspath(device_path)
        serial = get_serial(device_path)
        if serial is None:
            raise ValueError(f"device path {device_path} is not a valid device path")
        if name is None:
            name = serial

        dtype = get_type(device_path)
        if dtype is None:
            raise ValueError(f"device path {device_path} can not get type")

        add_time = datetime.now()
        last_check_time = LAST_CHECK_TIME_ORIGIN
        capacity = get_capacity(device_path)
        if capacity is None:
            raise ValueError(f"device path {device_path} cannot get capacity")

        state = get_healthy(device_path)

        device = device_factory.new_device(
            serial=serial,
            name=name,
            type=dtype,
            add_time=add_time,
            last_check_time=last_check_time,
            capacity=capacity,
            info=info,
            state=state,
            device_path=device_path,
        )

        if self.device_repository.is_exist(device):
            raise ValueError(f"device {serial} at {device_path} already exists")

        self.device_repository.reg_device(device)
        log_event(DeviceRegistered(device))
        return device.to_json()

    @staticmethod
    def _parse_state(state: str | DeviceState | None) -> DeviceState:
        if state is None:
            return DeviceState.UNKNOWN
        if isinstance(state, DeviceState):
            return state
        try:
            return DeviceState[state.upper()]
        except KeyError:
            return DeviceState.UNKNOWN

    def reg_device_by_info(
        self,
        serial: str,
        name: str | None,
        type: str | None,
        add_time: datetime | None,
        last_check_time: datetime | None,
        capacity: int | None,
        info: str | None,
        state: str | DeviceState | None,
        device_path: str | None = None,
    ) -> str:
        if name is None:
            name = serial[:8]
        if add_time is None:
            add_time = datetime.now()
        if last_check_time is None:
            last_check_time = LAST_CHECK_TIME_ORIGIN

        state = self._parse_state(state)

        if device_path:
            device_path = os.path.abspath(device_path)
        device = device_factory.new_device(
            serial=serial,
            name=name,
            type=type,
            add_time=add_time,
            last_check_time=last_check_time,
            capacity=capacity,
            info=info,
            state=state,
            device_path=device_path,
        )
        if self.device_repository.is_exist(device):
            raise ValueError(f"device {serial} already exists")
        self.device_repository.reg_device(device)
        log_event(DeviceRegistered(device))
        return device.to_json()

    def load_device(
        self,
        serial: str | None = None,
        device_path: str | None = None,
    ) -> str | None:
        device = device_factory.load_device(serial=serial, device_path=device_path)
        return device.to_json() if device else None

    def load_device_by_target(self, target: str, field: str | None = None) -> str | None:
        """根据目标值加载设备。

        参数:
            target: 目标值（路径、序列号，后续可扩展为其他字段）。
            field:  指定匹配的字段名，None 表示自动识别（路径或序列号）。
        """
        if field is None:
            if is_path(target):
                return self.load_device(device_path=target, serial=None)
            return self.load_device(serial=target, device_path=None)
        # TODO: 按指定字段查询
        raise NotImplementedError(f"按字段 {field} 查询尚未实现")

    def list_devices(self) -> list[str]:
        return [device.to_json() for device in self.device_repository.list_devices()]

    # ── 字段更新（TODO） ──────────────────────────────────────────

    def set_name(self, serial: str, name: str) -> tuple[str, str]:
        """更新设备名称。返回 (旧值, 新值)。"""
        device = self.device_repository.load_device(serial)
        if device is None:
            raise ValueError(f"device {serial} not found")
        old = device.name
        self.device_repository.update_device(serial, name=name)
        log_event(DeviceFieldUpdated(serial, "name", old, name))
        return (old, name)

    def set_type(self, serial: str, type: str) -> tuple[str, str]:
        """更新设备类型。返回 (旧值, 新值)。"""
        device = self.device_repository.load_device(serial)
        if device is None:
            raise ValueError(f"device {serial} not found")
        old = device.dtype
        self.device_repository.update_device(serial, type=type)
        log_event(DeviceFieldUpdated(serial, "type", old, type))
        return (old, type)

    def set_state(self, serial: str, state: DeviceState) -> tuple[DeviceState, DeviceState]:
        """更新设备状态。返回 (旧值, 新值)。"""
        device = self.device_repository.load_device(serial)
        if device is None:
            raise ValueError(f"device {serial} not found")
        old = device.state
        self.device_repository.update_device(serial, state=state)
        log_event(DeviceFieldUpdated(serial, "state", old, state))
        return (old, state)

    def set_capacity(self, serial: str, capacity: int) -> tuple[int, int]:
        """更新设备容量。返回 (旧值, 新值)。"""
        device = self.device_repository.load_device(serial)
        if device is None:
            raise ValueError(f"device {serial} not found")
        old = device.capacity
        self.device_repository.update_device(serial, capacity=capacity)
        log_event(DeviceFieldUpdated(serial, "capacity", old, capacity))
        return (old, capacity)

    # ── info 操作（JSON 文本） ────────────────────────────────────

    @staticmethod
    def _parse_info(info_str: str | None) -> dict:
        """解析 info JSON 文本为字典，空值返回空字典。"""
        if not info_str:
            return {}
        try:
            return json.loads(info_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_info(self, serial: str, info: dict) -> tuple[dict, dict]:
        """全量替换 info（JSON 文本）。返回 (旧info, 新info)。"""
        device = self.device_repository.load_device(serial)
        if device is None:
            raise ValueError(f"device {serial} not found")
        old = self._parse_info(device.info)
        new_str = json.dumps(info, ensure_ascii=False)
        self.device_repository.update_device(serial, info=new_str)
        log_event(DeviceInfoSet(serial, old, info))
        return (old, info)

    def append_info(self, serial: str, data: dict) -> tuple[dict, dict]:
        """合并键值对到现有 info（JSON 文本）。返回 (旧info, 新info)。"""
        device = self.device_repository.load_device(serial)
        if device is None:
            raise ValueError(f"device {serial} not found")
        old = self._parse_info(device.info)
        new_info = {**old, **data}
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.device_repository.update_device(serial, info=new_str)
        log_event(DeviceInfoAppended(serial, old, new_info))
        return (old, new_info)

    def delete_info(self, serial: str, key: str) -> tuple[dict, dict]:
        """从 info 中删除指定键（JSON 文本）。返回 (旧info, 新info)。"""
        device = self.device_repository.load_device(serial)
        if device is None:
            raise ValueError(f"device {serial} not found")
        old = self._parse_info(device.info)
        new_info = dict(old)
        new_info.pop(key, None)
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.device_repository.update_device(serial, info=new_str)
        log_event(DeviceInfoKeyDeleted(serial, old, new_info, key))
        return (old, new_info)

    def set_serial(self, old_serial: str, new_serial: str) -> tuple[str, str]:
        """重置设备序列号，同步更新关联表。返回 (旧序列号, 新序列号)。"""
        if not self.device_repository.is_exist(old_serial):
            raise ValueError(f"device {old_serial} not found")
        self.device_repository.update_serial(old_serial, new_serial)
        log_event(DeviceSerialChanged(old_serial=old_serial, new_serial=new_serial))
        return (old_serial, new_serial)
        


