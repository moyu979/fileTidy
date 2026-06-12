"""
领域工厂：根据 svtype 字段创建对应的 SuperVolume 子类实例
"""

from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.variants.manual_copy import ManualCopySuperVolume
from domain.storage.super_volume.variants.stack import StackSuperVolume

_svtype_map = {
    "manual_copy": ManualCopySuperVolume,
    "stack": StackSuperVolume,
}


def super_volume_from_dict(data: dict) -> SuperVolume:
    """从字典重建对应子类的 SuperVolume 实例"""
    serial = data.get("serial")
    if not serial:
        raise ValueError("super_volume_from_dict: missing required field 'serial'")

    cls = _svtype_map.get(data.get("type"), SuperVolume)
    return cls(
        serial=serial,
        name=data.get("name", ""),
        svtype=data.get("type"),
        method=data.get("method", ""),
        add_time=data.get("add_time"),
        last_check_time=data.get("last_check_time"),
        state=data.get("state"),
        info=data.get("info", ""),
        volumes=data.get("volumes", []),
    )


def create_super_volume(
    *,
    serial: str,
    name: str = "",
    svtype: str | None = None,
    method: str = "",
    add_time=None,
    last_check_time=None,
    state=None,
    info=None,
    volumes: list[str] | None = None,
) -> SuperVolume:
    """所有字段显式传入，创建对应子类的 SuperVolume 实例"""
    if not serial:
        raise ValueError("create_super_volume: 'serial' is required")

    cls = _svtype_map.get(svtype, SuperVolume)
    return cls(
        serial=serial,
        name=name,
        svtype=svtype,
        method=method,
        add_time=add_time,
        last_check_time=last_check_time,
        state=state,
        info=info or "",
        volumes=volumes or [],
    )
