from domain.storage.super_volume.base import SuperVolume


class SuperVolumeRegistered:
    def __init__(self, super_volume: SuperVolume):
        self.super_volume = super_volume.to_snapshot()
