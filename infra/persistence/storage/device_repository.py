from ssl import SSLSession
from domain.storage.device.base import Device
from domain.storage.device.device_repo import device_repository_abc
from infra.persistence.database import session_scope
from infra.persistence.models import DeviceModel

class device_repository(device_repository_abc):
    def __init__(self,session_factory) -> None:
        self.session_factory = session_factory
        super().__init__()

    def is_exist(self, device: Device) -> bool:
        with session_scope(self.session_factory) as session:
            return session.query(DeviceModel).filter(DeviceModel.serial == device.serial).first() is not None

    def reg_device(self, device: Device) -> None:
        # 这里需要用device初始化一个DeviceModel
        device_model = DeviceModel(
                serial=device.serial,
                name=device.name,
                kind=device.kind,
                add_time=device.add_time,
                last_check_time=device.last_check_time,
                capacity=device.capacity,
                info=device.info,
                state=device.state,
            )
        with session_scope(self.session_factory) as session:
            session.add(device_model)
            session.commit()
            
