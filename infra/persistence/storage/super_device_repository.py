from typing import Any

from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.factory import super_device_from_dict
from domain.storage.super_device.repo import super_device_repository_abc
from infra.persistence.database import session_scope
from infra.persistence.models import DeviceStructureModel, RelationState, SuperDeviceModel

class super_device_repository(super_device_repository_abc):
    def __init__(self,session_factory) -> None:
        self.session_factory = session_factory
        super().__init__()
    def is_exist(self, super_device: SuperDevice | str) -> bool:
        if isinstance(super_device, SuperDevice):
            serial = super_device.serial
        else:
            serial = super_device
        with session_scope(self.session_factory) as session:
            return session.query(SuperDeviceModel).filter(SuperDeviceModel.serial == serial).first() is not None
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

    @staticmethod
    def _model_to_dict(model: SuperDeviceModel, device_ids: list[str]) -> dict[str, Any]:
        return {
            "serial": model.serial,
            "name": model.name,
            "type": model.type,
            "need_all_devices_online": model.need_all_devices_online,
            "add_time": model.add_time,
            "last_check_time": model.last_check_time,
            "state": model.state,
            "capacity": model.capacity,
            "info": model.info,
            "devices": device_ids,
        }

    def get_super_device(self, super_device_serial: str) -> SuperDevice | None:
        with session_scope(self.session_factory) as session:
            model = session.query(SuperDeviceModel).filter(
                SuperDeviceModel.serial == super_device_serial
            ).first()
            if model is None:
                return None
            structure_rows = session.query(DeviceStructureModel).filter(
                DeviceStructureModel.super_device_id == super_device_serial,
                DeviceStructureModel.state == RelationState.USING,
            ).all()
            device_ids = [row.sub_device_id for row in structure_rows]
            data = self._model_to_dict(model, device_ids)
            return super_device_from_dict(data)


    def list_super_device(self) -> list[SuperDevice]:
        with session_scope(self.session_factory) as session:
            models = session.query(SuperDeviceModel).all()
            result = []
            for model in models:
                structure_rows = session.query(DeviceStructureModel).filter(
                    DeviceStructureModel.super_device_id == model.serial,
                    DeviceStructureModel.state == RelationState.USING,
                ).all()
                device_ids = [row.sub_device_id for row in structure_rows]
                data = self._model_to_dict(model, device_ids)
                result.append(super_device_from_dict(data))
            return result
            
    