from __future__ import annotations

from datetime import datetime

from domain.storage.super_device.base import SuperDevice


class SuperDeviceRegistered:
    def __init__(self, super_device: SuperDevice):
        self.device = super_device.to_snapshot()
        self.timestamp = datetime.utcnow()


class SuperDeviceFieldUpdated:
    """超级设备普通字段更新事件。"""
    def __init__(self, serial: str, field: str, old_value, new_value):
        self.serial = serial
        self.field = field
        self.old_value = old_value
        self.new_value = new_value
        self.timestamp = datetime.utcnow()


class SuperDeviceInfoSet:
    """info 全量替换事件。"""
    def __init__(self, serial: str, old_info: dict, new_info: dict):
        self.serial = serial
        self.old_info = old_info
        self.new_info = new_info
        self.changed_keys = sorted(set(old_info) | set(new_info))
        self.timestamp = datetime.utcnow()


class SuperDeviceInfoAppended:
    """info 追加键值对事件。"""
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


class SuperDeviceInfoKeyDeleted:
    """info 删除键事件。"""
    def __init__(self, serial: str, old_info: dict, new_info: dict, deleted_key: str):
        self.serial = serial
        self.deleted_key = deleted_key
        self.old_value = old_info.get(deleted_key, "--")
        self.changed_keys = [deleted_key]
        self.timestamp = datetime.utcnow()


class SuperDeviceDeviceChanged:
    """超级设备的子设备变更事件（新增 / 移除 / 替换）。

    - 新增设备: old=None, new=<设备serial>
    - 移除设备: old=<设备serial>, new=None
    - 替换设备: old=<旧设备serial>, new=<新设备serial>
    """
    def __init__(self, super_device_serial: str, old: str | None, new: str | None):
        self.super_device_serial = super_device_serial
        self.old = old
        self.new = new
        self.timestamp = datetime.utcnow()