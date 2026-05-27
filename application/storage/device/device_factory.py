from datetime import datetime
import logging

from infra.persistence.storage import device_repository
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN
from domain.storage.device.base import Device
from domain.storage.device.factory import create_device, device_from_dict
from domain.storage.device.enum import DeviceState
from infra.system.storage.device.get_serial import get_serial
from infra.system.storage.device.get_path import get_path

logger = logging.getLogger(__name__)

class device_factory:
    
    device_repository: device_repository

    @classmethod
    def set_device_repository(cls, device_repository: device_repository) -> None:
        cls.device_repository = device_repository

    def __init__(self) -> None:
        pass

    @classmethod
    def load_device(
        cls,
        serial: str | None = None,
        device_path: str | None = None,
    ) -> Device | None:
        if serial is None and device_path is not None:
            serial = get_serial(device_path)
        if serial is None:
            raise ValueError("serial and device_path are both None")

        device = cls.device_repository.load_device(serial)
        if device is None:
            return None
        # 从 repo 拿到的已经是正确子类，只需补上 device_path
        device.device_path = device_path
        return device

    # 生成一个新的device对象  
    @staticmethod
    def new_device(
        serial: str|None,
        name: str,
        type: str|None,
        add_time,
        last_check_time,
        capacity: int|None,
        info: str|None,
        state: str|None,
        device_path: str|None,
        ) -> Device:
        if serial is None:
            raise ValueError("serial is None")

        if device_path is None:
            device_path = get_path(serial)

        if add_time is None:
            add_time = datetime.now()

        if last_check_time is None:
            last_check_time = LAST_CHECK_TIME_ORIGIN

        if info is None:
            info = ""
        if name is None:
            name = serial[:8]

        # state：字符串 → DeviceState 枚举
        if isinstance(state, str):
            state_map = {
                "health": DeviceState.HEALTHY,
                "danger": DeviceState.DANGER,
                "fault": DeviceState.FAULT,
                "no_longer_used": DeviceState.REMOVED,
                "removed": DeviceState.REMOVED,
            }
            state = state_map.get(state)
        if state is None:
            state = DeviceState.HEALTHY

        device = create_device(
            serial=serial,
            name=name,
            dtype=type,
            add_time=add_time,
            last_check_time=last_check_time,
            capacity=capacity,
            info=info,
            state=state,
            device_path=device_path,
        )

        logger.info(f"成功构造设备: {device}")
        return device




        