from __future__ import annotations

from datetime import datetime

from domain.storage.device.base import Device


class DeviceRegistered:
    def __init__(self, device: Device):
        self.device = device.to_snapshot()
        self.timestamp = datetime.utcnow()


class DeviceFieldUpdated:
    """设备普通字段更新事件（name / type / state / capacity）。"""
    def __init__(self, serial: str, field: str, old_value, new_value):
        self.serial = serial
        self.field = field
        self.old_value = old_value
        self.new_value = new_value
        self.timestamp = datetime.utcnow()


class DeviceInfoSet:
    """info 全量替换事件。"""
    def __init__(self, serial: str, old_info: dict, new_info: dict):
        self.serial = serial
        self.old_info = old_info
        self.new_info = new_info
        self.changed_keys = sorted(set(old_info) | set(new_info))
        self.timestamp = datetime.utcnow()


class DeviceInfoAppended:
    """info 追加键值对事件。只记录实际发生变化的 key。"""
    def __init__(self, serial: str, old_info: dict, new_info: dict):
        self.serial = serial
        self.changed_data = {
            k: {"old": old_info.get(k, "--"), "new": new_info.get(k, "--")}
            for k in (set(old_info) | set(new_info))
            if old_info.get(k) != new_info.get(k)
        }
        self.timestamp = datetime.utcnow()

    @property
    def changed_keys(self) -> list[str]:
        return sorted(self.changed_data)


class DeviceInfoKeyDeleted:
    """info 删除键事件。"""
    def __init__(self, serial: str, old_info: dict, new_info: dict, deleted_key: str):
        self.serial = serial
        self.deleted_key = deleted_key
        self.old_value = old_info.get(deleted_key, "--")
        self.changed_keys = [deleted_key]
        self.timestamp = datetime.utcnow()


class DeviceSerialChanged:
    """设备序列号变更事件。"""
    def __init__(self, old_serial: str, new_serial: str):
        self.old_serial = old_serial
        self.new_serial = new_serial
        self.timestamp = datetime.utcnow()