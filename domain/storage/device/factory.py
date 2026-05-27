"""
领域工厂：根据 type 字段创建对应的 Device 子类实例
"""

from domain.storage.device.base import Device
from domain.storage.device.variants.HDD import HddDevice
from domain.storage.device.variants.SSD import SsdDevice
from domain.storage.device.variants.Tape import TapeDevice
from domain.storage.device.variants.TfSd import TfSdCardDevice

_type_map = {
    "hdd": HddDevice,
    "ssd": SsdDevice,
    "tape": TapeDevice,
    "tf_sd_card": TfSdCardDevice,
}


def device_from_dict(data: dict, device_path: str | None = None) -> Device:
    """从字典重建对应子类的 Device 实例"""
    serial = data.get("serial")
    if not serial:
        raise ValueError("device_from_dict: missing required field 'serial'")

    cls = _type_map.get(data.get("type"), Device)
    return cls(
        serial=serial,
        name=data.get("name", ""),
        dtype=data.get("type"),
        add_time=data.get("add_time"),
        last_check_time=data.get("last_check_time"),
        capacity=data.get("capacity"),
        info=data.get("info"),
        state=data.get("state"),
        device_path=device_path if device_path is not None else data.get("device_path"),
    )


def create_device(
    *,
    serial: str,
    name: str = "",
    dtype: str | None = None,
    add_time=None,
    last_check_time=None,
    capacity=None,
    info=None,
    state=None,
    device_path=None,
) -> Device:
    """所有字段显式传入，创建对应子类的 Device 实例"""
    if not serial:
        raise ValueError("create_device: 'serial' is required")

    cls = _type_map.get(dtype, Device)
    return cls(
        serial=serial,
        name=name,
        dtype=dtype,
        add_time=add_time,
        last_check_time=last_check_time,
        capacity=capacity,
        info=info,
        state=state,
        device_path=device_path,
    )
