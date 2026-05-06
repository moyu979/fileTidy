from domain.storage.volume.base import Volume


class VolumeRegistered:
    def __init__(self, volume: Volume):
        self.volume = volume.to_snapshot()