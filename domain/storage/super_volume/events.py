from domain.storage.super_volume.base import SuperVolume


class SuperVolumeRegistered:
    def __init__(self, super_volume: SuperVolume):
        self.super_volume = super_volume.to_snapshot()


class VolumesAddedToSuperVolume:
    """卷被添加到超级卷时触发"""

    def __init__(self, super_volume_serial: str, volume_ids: list[str]) -> None:
        self.super_volume_serial = super_volume_serial
        self.volume_ids = list(volume_ids)

    def to_snapshot(self) -> dict:
        return {
            "super_volume_serial": self.super_volume_serial,
            "volume_ids": list(self.volume_ids),
        }
