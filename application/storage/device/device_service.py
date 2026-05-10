from datetime import datetime
import logging
import os
from application.storage.device.device_factory import device_factory
from infra.system.storage.device.get_healthy import get_healthy
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN
from domain.storage.device.base import Device
from domain.storage.device.events import DeviceRegistered
from infra.operate_log.operate_log import log_event
from domain.storage.device.enum import DeviceState
from infra.system.storage.device.get_capacity import get_capacity
from infra.system.storage.device.get_serial import get_serial
from infra.system.storage.device.get_type import get_type

logger = logging.getLogger(__name__)

class device_service:   
    def __init__(self,device_repository) -> None:
        self.device_repository = device_repository
        logger.info("Device service initialized")

    def reg_device_by_path(self, 
        device_path: str,
        name: str|None,
        info: str|None,
    ) -> None:

        device_path=os.path.abspath(device_path)
        serial = get_serial(device_path)
        if serial is None:
            raise ValueError(f"device path {device_path} is not a valid device path")
        if name is None:
            name=serial

        type = get_type(device_path)
        if type is None:
            raise ValueError(f"device path {device_path} can not get type")
        
        add_time = datetime.now()

        last_check_time = LAST_CHECK_TIME_ORIGIN

        capacity = get_capacity(device_path)
        if capacity is None:
            raise ValueError(f"device path {device_path} cannot get capacity")

        state = get_healthy(device_path)

        device = device_factory.new_device(
            serial=serial,
            name=name,
            type=type,
            add_time=add_time,
            last_check_time=last_check_time,
            capacity=capacity,
            info=info,
            state=state,
            device_path=device_path,
        )

        if self.device_repository.is_exist(device):
            raise ValueError(f"device {serial} at {device_path} already exists")

        self.device_repository.reg_device(device)
        log_event(DeviceRegistered(device))
        return device.to_json()

    def reg_device_by_info(self,
        serial: str,
        name: str|None,
        type: str|None,
        add_time: datetime|None,
        last_check_time: datetime|None,
        capacity: int|None,
        info: str|None,
        state: str|None,
        device_path: str|None,
    ) -> None:
        if name is None:
            name = serial[:8]
        if add_time is None:
            add_time = datetime.now()
        if last_check_time is None:
            last_check_time = LAST_CHECK_TIME_ORIGIN
        device = device_factory.new_device(
            serial=serial,
            name=name,
            type=type,
            add_time=add_time,
            last_check_time=last_check_time,
            capacity=capacity,  
            info=info,
            state=state,
            device_path=device_path,
        )
        if self.device_repository.is_exist(device):
            raise ValueError(f"device {serial} already exists")
        self.device_repository.reg_device(device)
        log_event(DeviceRegistered(device))
        return device.to_json()

    def load_device(self,
        serial: str|None,
        device_path: str|None,
    ) -> Device | None:
        device=device_factory.load_device(
            serial=serial,
            device_path=device_path,
        )
        return device.to_json() if device else None

    def list_devices(self) -> list[Device]:
        return [device.to_json() for device in self.device_repository.list_devices()]
        


