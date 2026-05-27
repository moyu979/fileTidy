"""
领域工厂：根据 sdtype 字段创建对应的 SuperDevice 子类实例
"""

from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.variants.single_super_device import SingleSuperDevice
from domain.storage.super_device.variants.raidz import RaidzSuperDevice

_sdtype_map = {
    "single": SingleSuperDevice,
    "raidz": RaidzSuperDevice,
}


def super_device_from_dict(data: dict) -> SuperDevice:
    """从字典重建对应子类的 SuperDevice 实例"""
    serial = data.get("serial")
    if not serial:
        raise ValueError("super_device_from_dict: missing required field 'serial'")

    cls = _sdtype_map.get(data.get("type"), SuperDevice)
    return cls(
        serial=serial,
        name=data.get("name", ""),
        sdtype=data.get("type"),
        need_all_devices_online=data.get("need_all_devices_online", False),
        add_time=data.get("add_time"),
        last_check_time=data.get("last_check_time"),
        state=data.get("state"),
        capacity=data.get("capacity"),
        info=data.get("info"),
        devices=data.get("devices", []),
    )


def create_super_device(
    *,
    serial: str,
    name: str = "",
    sdtype: str | None = None,
    need_all_devices_online: bool = False,
    add_time=None,
    last_check_time=None,
    state=None,
    capacity=None,
    info=None,
    devices: list[str] | None = None,
) -> SuperDevice:
    """所有字段显式传入，创建对应子类的 SuperDevice 实例"""
    if not serial:
        raise ValueError("create_super_device: 'serial' is required")

    cls = _sdtype_map.get(sdtype, SuperDevice)
    return cls(
        serial=serial,
        name=name,
        sdtype=sdtype,
        need_all_devices_online=need_all_devices_online,
        add_time=add_time,
        last_check_time=last_check_time,
        state=state,
        capacity=capacity,
        info=info,
        devices=devices or [],
    )
