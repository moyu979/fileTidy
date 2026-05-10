from domain.storage.super_device.base import SuperDevice


class SuperDeviceRegistered:
    def __init__(self, super_device: SuperDevice):
        self.device = super_device.to_snapshot()