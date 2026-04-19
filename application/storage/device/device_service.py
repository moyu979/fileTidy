
import datetime
import logging
from application.storage.device.device_factory import device_factory
from domain.storage.device.events import DeviceRegistered
from infra.operate_log.operate_log import log_event

logger = logging.getLogger(__name__)

class device_service:   
    def __init__(self,device_repository) -> None:
        self.device_repository = device_repository
        logger.info("Device service initialized")

    def reg_device(self, 
        serial: str,
        name: str,
        type: str,
        add_time,
        last_check_time,
        capacity: int|None,
        info: str|None,
        state: str|None,
        device_path: str|None,
    ) -> None:
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
        return device
