"""
领域工厂：根据 file_system 字段创建对应的 Volume 子类实例
"""

from domain.storage.volume.base import Volume
from domain.storage.volume.variants.ntfs import NtfsVolume
from domain.storage.volume.variants.exfat import ExfatVolume
from domain.storage.volume.variants.fat32 import Fat32Volume
from domain.storage.volume.variants.ltfs import LtfsVolume

_filesystem_map = {
    "ntfs": NtfsVolume,
    "exfat": ExfatVolume,
    "fat32": Fat32Volume,
    "ltfs": LtfsVolume,
}


def volume_from_dict(data: dict, volume_path: str | None = None) -> Volume:
    """从字典重建对应子类的 Volume 实例"""
    serial = data.get("serial")
    if not serial:
        raise ValueError("volume_from_dict: missing required field 'serial'")

    cls = _filesystem_map.get(data.get("file_system"), Volume)
    return cls(
        serial=serial,
        device_id=data.get("device_id", ""),
        name=data.get("name", ""),
        add_time=data.get("add_time"),
        last_check_time=data.get("last_check_time"),
        state=data.get("state"),
        capacity=data.get("capacity"),
        unique_mount_point=data.get("unique_mount_point"),
        file_system=data.get("file_system"),
        info=data.get("info"),
        volume_path=volume_path if volume_path is not None else data.get("volume_path"),
    )


def create_volume(
    *,
    serial: str,
    device_id: str = "",
    name: str = "",
    add_time=None,
    last_check_time=None,
    state=None,
    capacity=None,
    unique_mount_point=None,
    file_system: str | None = None,
    info=None,
    volume_path=None,
) -> Volume:
    """所有字段显式传入，创建对应子类的 Volume 实例"""
    if not serial:
        raise ValueError("create_volume: 'serial' is required")

    cls = _filesystem_map.get(file_system, Volume)
    return cls(
        serial=serial,
        device_id=device_id,
        name=name,
        add_time=add_time,
        last_check_time=last_check_time,
        state=state,
        capacity=capacity,
        unique_mount_point=unique_mount_point,
        file_system=file_system,
        info=info,
        volume_path=volume_path,
    )
