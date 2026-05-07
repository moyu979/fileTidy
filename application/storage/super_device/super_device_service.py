from datetime import datetime
import logging

from application.storage.super_device.super_device_factory import super_device_factory
from infra.persistence.models import SuperDeviceState
from infra.persistence.storage import super_device_repository
from infra.system.path_manager.is_path import is_path
from infra.system.storage.device import get_serial
from shared.id_generator import generate_id
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN

logger = logging.getLogger(__name__)

class super_device_service:   
    def __init__(self,device_repository) -> None:
        self.super_device_repository = super_device_repository
        logger.info("super_device service initialized")

    def reg_super_device(self, 
        name: str,
        type: str,
        need_all_devices_online: bool,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperDeviceState,
        capacity: int,
        devices: list[str],
        info: str,
    ) -> None:
        serial = generate_id("")
        if name is None:
            name = serial[:8]
        if type is None:
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
            serial=serial,
            name=name,
            type=type,
            need_all_devices_online=need_all_devices_online,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            capacity=capacity,
            info=info,
            devices=devices,
        )

        self.super_device_repository.reg_super_device(super_device)





        
            
    
