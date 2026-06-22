from typing import Any

from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.factory import super_device_from_dict
from domain.storage.super_device.repo import super_device_repository_abc
from infra.persistence.database import session_scope
from infra.persistence.models import DeviceStructureModel, RelationState, SuperDeviceModel


def _parse_structure_info(info_str: str | None) -> dict:
    """解析 DeviceStructureModel.info JSON 文本。"""
    if not info_str:
        return {}
    import json
    try:
        return json.loads(info_str)
    except (json.JSONDecodeError, TypeError):
        return {}


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

    # 领域字段名 → 模型列名 映射
    _field_mapping = {
        "sdtype": "type",
    }

    def update_super_device(self, serial: str, **fields) -> None:
        """更新超级设备指定字段。"""
        with session_scope(self.session_factory) as session:
            model = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == serial)
                .first()
            )
            if model is None:
                raise ValueError(f"super_device {serial} not found")
            for key, value in fields.items():
                col = self._field_mapping.get(key, key)
                setattr(model, col, value)
            session.commit()

    # ── 子设备管理 ────────────────────────────────────────────────

    def add_device(self, super_device_serial: str, device_serial: str, add_time) -> None:
        """向超级设备新增一个子设备。"""
        with session_scope(self.session_factory) as session:
            row = DeviceStructureModel(
                super_device_id=super_device_serial,
                sub_device_id=device_serial,
                add_time=add_time,
                state=RelationState.USING,
                info="",
            )
            session.add(row)
            session.commit()

    def replace_device(
        self, super_device_serial: str, old_device_serial: str,
        new_device_serial: str, add_time,
    ) -> None:
        """替换超级设备的子设备。"""
        with session_scope(self.session_factory) as session:
            # 1. 查找旧映射，标记 UNUSED
            old_row = (
                session.query(DeviceStructureModel)
                .filter(
                    DeviceStructureModel.super_device_id == super_device_serial,
                    DeviceStructureModel.sub_device_id == old_device_serial,
                    DeviceStructureModel.state == RelationState.USING,
                )
                .first()
            )
            if old_row is None:
                raise ValueError(
                    f"device {old_device_serial} not found in super_device {super_device_serial}"
                )
            old_row.state = RelationState.UNUSED

            # 2. 旧映射的 info 中记录 replaced_by
            old_info = _parse_structure_info(old_row.info)
            old_info["replaced_by"] = new_device_serial
            import json
            old_row.info = json.dumps(old_info, ensure_ascii=False)

            # 3. 新增新设备映射
            new_row = DeviceStructureModel(
                super_device_id=super_device_serial,
                sub_device_id=new_device_serial,
                add_time=add_time,
                state=RelationState.USING,
                info="",
            )
            session.add(new_row)
            session.commit()

    def remove_device(self, super_device_serial: str, device_serial: str) -> None:
        """从超级设备移除一个子设备（标记 UNUSED）。"""
        with session_scope(self.session_factory) as session:
            row = (
                session.query(DeviceStructureModel)
                .filter(
                    DeviceStructureModel.super_device_id == super_device_serial,
                    DeviceStructureModel.sub_device_id == device_serial,
                    DeviceStructureModel.state == RelationState.USING,
                )
                .first()
            )
            if row is None:
                raise ValueError(
                    f"device {device_serial} not found in super_device {super_device_serial}"
                )
            row.state = RelationState.UNUSED
            session.commit()