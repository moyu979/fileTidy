from datetime import datetime
import logging

from application.storage.super_device.factory import super_device_factory
from domain.storage.super_device.events import SuperDeviceRegistered
from infra.operate_log.operate_log import log_event
from domain.storage.super_device.enum import SuperDeviceState
from infra.persistence.storage.super_device_repository import super_device_repository
from infra.system.path_manager.is_path import is_path
from infra.system.storage.device import get_serial
from shared.id_generator import generate_id
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN

logger = logging.getLogger(__name__)

class super_device_service:   
    def __init__(self, super_device_repository) -> None:
        self.super_device_repository = super_device_repository
        logger.info("super_device service initialized")

    def reg_super_device(self, 
        name: str,
        sdtype: str,
        need_all_devices_online: bool,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperDeviceState,
        capacity: int,
        devices: list[str],
        info: str,
    ) -> None:
        super_device_serial = generate_id("")
        if name is None:
            name = super_device_serial[:8]
        if sdtype is None:
            raise ValueError("type is None")
        if need_all_devices_online is None:
            need_all_devices_online = True
        if add_time is None:
            add_time = datetime.now()
        if last_check_time is None:
            last_check_time = LAST_CHECK_TIME_ORIGIN
        if state is None:
            state = SuperDeviceState.HEALTHY
        if capacity is None:
            capacity = -1
        if info is None:
            info = ""
        sericals = []
        for device in devices:
            if is_path(device):
                serial = get_serial(device)
            else:
                serial = device
            sericals.append(serial)

        super_device = super_device_factory.new_super_device(
            serial=super_device_serial,
            name=name,
            sdtype=sdtype,
            need_all_devices_online=need_all_devices_online,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            capacity=capacity,
            info=info,
            devices=devices,
        )

        self.super_device_repository.reg_super_device(super_device)
        log_event(SuperDeviceRegistered(super_device))
        return super_device.to_json()

    def load_super_device(
        self,
        serial: str | None = None,
        super_device_path: str | None = None,
    ) -> str | None:
        if serial is None and super_device_path is not None:
            serial = get_serial(super_device_path)
        if serial is None:
            return None
        sd = self.super_device_repository.get_super_device(serial)
        return sd.to_json() if sd else None

    def list_super_devices(self) -> list[str]:
        return [sd.to_json() for sd in self.super_device_repository.list_super_device()]





        
            
    
    
