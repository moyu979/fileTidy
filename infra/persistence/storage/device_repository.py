from domain.storage.device.base import Device
from domain.storage.device.repo import device_repository_abc
from domain.storage.device.factory import device_from_dict
from infra.persistence.database import session_scope
from infra.persistence.models import DeviceModel, DeviceStructureModel, VolumeModel

class device_repository(device_repository_abc):
    def __init__(self,session_factory) -> None:
        self.session_factory = session_factory
        super().__init__()

    def is_exist(self, device: Device | str) -> bool:
        if isinstance(device, Device):
            serial = device.serial
        else:
            serial = device
        with session_scope(self.session_factory) as session:
            return session.query(DeviceModel).filter(DeviceModel.serial == serial).first() is not None

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

    def update_device(self, serial: str, **fields) -> None:
        """更新设备指定字段。"""
        with session_scope(self.session_factory) as session:
            device_model = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == serial)
                .first()
            )
            if device_model is None:
                raise ValueError(f"device {serial} not found")
            for key, value in fields.items():
                setattr(device_model, key, value)
            session.commit()

    def update_serial(self, old_serial: str, new_serial: str) -> None:
        """重置设备序列号，同步更新关联表中的外键引用。"""
        with session_scope(self.session_factory) as session:
            # 更新设备自身主键
            row = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == old_serial)
                .first()
            )
            if row is None:
                raise ValueError(f"device {old_serial} not found")
            session.delete(row)
            session.flush()

            row.serial = new_serial
            session.add(row)
            session.flush()

            # 更新 volumes 中引用的 device_id
            (
                session.query(VolumeModel)
                .filter(VolumeModel.device_id == old_serial)
                .update({"device_id": new_serial})
            )

            # 更新 device_structures 中引用的 sub_device_id
            (
                session.query(DeviceStructureModel)
                .filter(DeviceStructureModel.sub_device_id == old_serial)
                .update({"sub_device_id": new_serial})
            )

            session.commit()
