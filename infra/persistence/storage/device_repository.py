from domain.storage.device.base import Device
from domain.storage.device.repo import device_repository_abc
from domain.storage.device.factory import device_from_dict
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
                type=device.dtype,
                add_time=device.add_time,
                last_check_time=device.last_check_time,
                capacity=device.capacity,
                info=device.info,
                state=device.state,
            )
        with session_scope(self.session_factory) as session:
            session.add(device_model)
            session.commit()
            
    def load_device(self, serial: str) -> Device | None:
        with session_scope(self.session_factory) as session:
            device_model = session.query(DeviceModel).filter(DeviceModel.serial == serial).first()
            if device_model is None:
                return None
            return device_from_dict({
                "serial": device_model.serial,
                "name": device_model.name,
                "type": device_model.type,
                "add_time": device_model.add_time,
                "last_check_time": device_model.last_check_time,
                "capacity": device_model.capacity,
                "info": device_model.info,
                "state": device_model.state,
            })

    def list_devices(self) -> list[Device]:
        with session_scope(self.session_factory) as session:
            device_models = session.query(DeviceModel).all()
            return [
                device_from_dict({
                    "serial": device_model.serial,
                    "name": device_model.name,
                    "type": device_model.type,
                    "add_time": device_model.add_time,
                    "last_check_time": device_model.last_check_time,
                    "capacity": device_model.capacity,
                    "info": device_model.info,
                    "state": device_model.state,
                })
                for device_model in device_models
            ]
