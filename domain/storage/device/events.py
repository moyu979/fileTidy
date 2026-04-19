from domain.storage.device.base import Device


class DeviceRegistered:
    def __init__(self, device: Device):
        self.device = device.to_snapshot()