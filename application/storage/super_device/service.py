from datetime import datetime
import json
import logging

from application.storage.super_device.factory import super_device_factory
from domain.storage.super_device.events import (
    SuperDeviceDeviceChanged,
    SuperDeviceFieldUpdated,
    SuperDeviceInfoAppended,
    SuperDeviceInfoKeyDeleted,
    SuperDeviceInfoSet,
    SuperDeviceRegistered,
)
from infra.operate_log.operate_log import log_event
from domain.storage.super_device.enum import SuperDeviceState
from infra.persistence.storage.super_device_repository import super_device_repository
from infra.system.path_manager.is_path import is_path
from infra.system.storage.device.get_serial import get_serial
from shared.id_generator import generate_id
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN

logger = logging.getLogger(__name__)

class super_device_service:   
    def __init__(self, super_device_repository, device_repository=None) -> None:
        self.super_device_repository = super_device_repository
        self.device_repository = device_repository
        logger.info("super_device service initialized")

    def reg_super_device(self, 
        name: str,
        sdtype: str,
        need_all_devices_online: bool,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperDeviceState,
        capacity: int,
        devices: list[str],
        info: str,
    ) -> None:
        super_device_serial = generate_id("")
        if name is None:
            name = super_device_serial[:8]
        if sdtype is None:
            raise ValueError("type is None")
        if need_all_devices_online is None:
            need_all_devices_online = True
        if add_time is None:
            add_time = datetime.now()
        if last_check_time is None:
            last_check_time = LAST_CHECK_TIME_ORIGIN
        if state is None:
            state = SuperDeviceState.HEALTHY
        if capacity is None:
            capacity = -1
        if info is None:
            info = ""
        sericals = []
        for device in devices:
            if is_path(device):
                serial = get_serial(device)
            else:
                serial = device
            sericals.append(serial)

        super_device = super_device_factory.new_super_device(
            serial=super_device_serial,
            name=name,
            sdtype=sdtype,
            need_all_devices_online=need_all_devices_online,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            capacity=capacity,
            info=info,
            devices=devices,
        )

        self.super_device_repository.reg_super_device(super_device)
        log_event(SuperDeviceRegistered(super_device))
        return super_device.to_json()

    def load_super_device(
        self,
        serial: str | None = None,
        super_device_path: str | None = None,
    ) -> str | None:
        if serial is None and super_device_path is not None:
            serial = get_serial(super_device_path)
        if serial is None:
            return None
        sd = self.super_device_repository.get_super_device(serial)
        return sd.to_json() if sd else None

    def list_super_devices(self) -> list[str]:
        return [sd.to_json() for sd in self.super_device_repository.list_super_device()]

    # ── 字段更新 ──────────────────────────────────────────────────

    def set_name(self, serial: str, name: str) -> tuple[str, str]:
        """更新超级设备名称。返回 (旧值, 新值)。"""
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = sd.name
        self.super_device_repository.update_super_device(serial, name=name)
        log_event(SuperDeviceFieldUpdated(serial, "name", old, name))
        return (old, name)

    def set_sdtype(self, serial: str, sdtype: str) -> tuple[str, str]:
        """更新超级设备类型。返回 (旧值, 新值)。"""
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = sd.sdtype
        self.super_device_repository.update_super_device(serial, sdtype=sdtype)
        log_event(SuperDeviceFieldUpdated(serial, "sdtype", old, sdtype))
        return (old, sdtype)

    def set_state(self, serial: str, state: SuperDeviceState) -> tuple[SuperDeviceState, SuperDeviceState]:
        """更新超级设备状态。返回 (旧值, 新值)。"""
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = sd.state
        self.super_device_repository.update_super_device(serial, state=state)
        log_event(SuperDeviceFieldUpdated(serial, "state", old, state))
        return (old, state)

    def set_capacity(self, serial: str, capacity: int) -> tuple[int, int]:
        """更新超级设备容量。返回 (旧值, 新值)。"""
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = sd.capacity
        self.super_device_repository.update_super_device(serial, capacity=capacity)
        log_event(SuperDeviceFieldUpdated(serial, "capacity", old, capacity))
        return (old, capacity)

    def set_need_all_devices_online(self, serial: str, value: bool) -> tuple[bool, bool]:
        """更新是否需要全部设备同时上线。返回 (旧值, 新值)。"""
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = sd.need_all_devices_online
        self.super_device_repository.update_super_device(serial, need_all_devices_online=value)
        log_event(SuperDeviceFieldUpdated(serial, "need_all_devices_online", old, value))
        return (old, value)

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
        """全量替换 info。返回 (旧info, 新info)。"""
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = self._parse_info(sd.info)
        new_str = json.dumps(info, ensure_ascii=False)
        self.super_device_repository.update_super_device(serial, info=new_str)
        log_event(SuperDeviceInfoSet(serial, old, info))
        return (old, info)

    def append_info(self, serial: str, data: dict) -> tuple[dict, dict]:
        """合并键值对到现有 info。返回 (旧info, 新info)。"""
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = self._parse_info(sd.info)
        new_info = {**old, **data}
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.super_device_repository.update_super_device(serial, info=new_str)
        log_event(SuperDeviceInfoAppended(serial, old, new_info))
        return (old, new_info)

    def delete_info(self, serial: str, key: str) -> tuple[dict, dict]:
        """从 info 中删除指定键。返回 (旧info, 新info)。"""
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = self._parse_info(sd.info)
        new_info = dict(old)
        new_info.pop(key, None)
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.super_device_repository.update_super_device(serial, info=new_str)
        log_event(SuperDeviceInfoKeyDeleted(serial, old, new_info, key))
        return (old, new_info)

    # ── 子设备管理 ────────────────────────────────────────────────

    def _require_device(self, device_serial: str) -> None:
        """检查设备是否存在，不存在则抛异常。"""
        if self.device_repository is None:
            return
        if not self.device_repository.is_exist(device_serial):
            raise ValueError(f"子设备 {device_serial} 不存在")

    def add_device(self, super_device_serial: str, device_serial: str) -> None:
        """向超级设备新增一个子设备。"""
        sd = self.super_device_repository.get_super_device(super_device_serial)
        if sd is None:
            raise ValueError(f"super_device {super_device_serial} not found")
        self._require_device(device_serial)
        self.super_device_repository.add_device(super_device_serial, device_serial, datetime.now())
        log_event(SuperDeviceDeviceChanged(super_device_serial, old=None, new=device_serial))

    def replace_device(self, super_device_serial: str, old_device_serial: str, new_device_serial: str) -> None:
        """替换超级设备的子设备。"""
        sd = self.super_device_repository.get_super_device(super_device_serial)
        if sd is None:
            raise ValueError(f"super_device {super_device_serial} not found")
        self._require_device(new_device_serial)
        self.super_device_repository.replace_device(
            super_device_serial, old_device_serial, new_device_serial, datetime.now(),
        )
        log_event(SuperDeviceDeviceChanged(super_device_serial, old=old_device_serial, new=new_device_serial))

    def remove_device(self, super_device_serial: str, device_serial: str) -> None:
        """从超级设备移除一个子设备。"""
        sd = self.super_device_repository.get_super_device(super_device_serial)
        if sd is None:
            raise ValueError(f"super_device {super_device_serial} not found")
        self.super_device_repository.remove_device(super_device_serial, device_serial)
        log_event(SuperDeviceDeviceChanged(super_device_serial, old=device_serial, new=None))
