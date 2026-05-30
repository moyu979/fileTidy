"""
设备工厂 —— 去掉 DeviceSystemPort 依赖，直接调用系统函数。
保留类结构和 set_device_repository()，仓库保持原样。
"""

from datetime import datetime
import logging

from infra.persistence.storage import device_repository
from infra.system.storage.device.get_serial import get_serial
from infra.system.storage.device.get_path import get_path
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN
from domain.storage.device.base import Device
from domain.storage.device.factory import create_device
from domain.storage.device.enum import DeviceState

logger = logging.getLogger(__name__)


class device_factory:

    device_repository: device_repository

    @classmethod
    def set_device_repository(cls, repo: device_repository) -> None:
        cls.device_repository = repo

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
        device.device_path = device_path
        return device

    @classmethod
    def new_device(
        cls,
        serial: str | None,
        name: str,
        type: str | None,
        add_time,
        last_check_time,
        capacity: int | None,
        info: str | None,
        state: str | None,
        device_path: str | None,
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




        