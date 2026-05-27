from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.repo import super_device_repository_abc
from infra.persistence.database import session_scope
from infra.persistence.models import DeviceStructureModel, RelationState, SuperDeviceModel

class super_device_repository(super_device_repository_abc):
    def __init__(self,session_factory) -> None:
        self.session_factory = session_factory
        super().__init__()

    def reg_super_device(self, super_device: SuperDevice) -> None:
        super_device_model = SuperDeviceModel(
            serial=super_device.serial,
            name=super_device.name,
            type=super_device.sdtype,
            need_all_devices_online=super_device.need_all_devices_online,
            add_time=super_device.add_time,
            last_check_time=super_device.last_check_time,
            state=super_device.state,
            capacity=super_device.capacity,
            info=super_device.info,
        )
        with session_scope(self.session_factory) as session:
            session.add(super_device_model)
            session.commit()
        devices=[]
        for device in super_device.devices:
            device_structure_model = DeviceStructureModel(
                super_device_id=super_device.serial,
                sub_device_id=device,
                add_time=super_device.add_time,
                state=RelationState.USING,
                info=super_device.info,
            )
            devices.append(device_structure_model)
        with session_scope(self.session_factory) as session:
            session.add_all(devices)
            session.commit()
            
    