from datetime import datetime
import logging
from tkinter import NO

from infra.persistence.storage import device_repository
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN
from domain.storage.device.base import Device
from infra.persistence.database import session_scope
from infra.persistence.models import DeviceModel, DeviceState
from domain.storage.device.variants.HDD import HddDevice
from domain.storage.device.variants.SSD import SsdDevice
from domain.storage.device.variants.Tape import TapeDevice
from domain.storage.device.variants.TfSd import TfSdCardDevice
from infra.system.storage.device.get_serial import get_serial
from infra.system.storage.device.get_path import get_path
from infra.system.storage.device.get_type import get_type
from infra.system.storage.device.get_capacity import get_capacity

logger = logging.getLogger(__name__)

class device_factory:
    def __init__(self) -> None:
        pass

    @staticmethod
    def load_device(
        serial: str | None,
        device_path: str | None,
        device_repository: device_repository,
    ) -> Device | None:
        if serial is None and device_path is not None:
            serial = get_serial(device_path)
        if serial is None:
            raise ValueError("serial and device_path are both None")

        device_dict = device_repository.load_device(serial)
        if device_dict is None:
            return None
        else:
            if device_dict["type"] == "hdd":
                return HddDevice(
                    serial=device_dict["serial"],
                    name=device_dict["name"],
                    type=device_dict["type"],
                    add_time=device_dict["add_time"],
                    last_check_time=device_dict["last_check_time"],
                    capacity=device_dict["capacity"],
                    info=device_dict["info"],
                    state=device_dict["state"],
                    device_path=device_path,
                )
            if device_dict["type"] == "tf_sd_card":
                return TfSdCardDevice(
                    serial=device_dict["serial"],
                    name=device_dict["name"],
                    type=device_dict["type"],
                    add_time=device_dict["add_time"],
                    last_check_time=device_dict["last_check_time"],
                    capacity=device_dict["capacity"],
                    info=device_dict["info"],
                    state=device_dict["state"],
                    device_path=device_path,
                )
            if device_dict["type"] == "tape":
                return TapeDevice(
                    serial=device_dict["serial"],
                    name=device_dict["name"],
                    type=device_dict["type"],
                    add_time=device_dict["add_time"],
                    last_check_time=device_dict["last_check_time"],
                    capacity=device_dict["capacity"],
                    info=device_dict["info"],
                    state=device_dict["state"],
                    device_path=device_path,
                )
            if device_dict["type"] == "any":
                return Device(
                    serial=device_dict["serial"],
                    name=device_dict["name"],
                    type=device_dict["type"],
                    add_time=device_dict["add_time"],
                    last_check_time=device_dict["last_check_time"],
                    capacity=device_dict["capacity"],
                    info=device_dict["info"],
                    state=device_dict["state"],
                    device_path=device_path,
                )
            raise ValueError(f"invalid type: {device_dict["type"]}")

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
        # 如果设备的路径为空，有两种可能，
        # 一种是，其他所有必要信息均已经提供，此时，路径可以不填
        # 对另一种，是需要由序列号进行推断
        # 但是总之，这里选择尝试去获取一下路径，如果路径能够获取，就使用获取到的路径，如果路径不能获取，就尝试无路径推断
        if serial is None:
            raise ValueError("serial is None")

        if device_path is None:
            # 有可能依旧为None
            device_path = get_path(serial)

        if add_time is None:
            add_time = datetime.now()

        if last_check_time is None:
            last_check_time = LAST_CHECK_TIME_ORIGIN
            
        if info is None:
            info = ""

        device=None
        if type=="ssd":
            device = SsdDevice(
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
        elif type=="hdd":
            device = HddDevice(
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
        elif type=="tf_sd_card":
            device = TfSdCardDevice(
                serial=serial,
                name=name,
                kind=type,
                add_time=add_time,
                last_check_time=last_check_time,
                capacity=capacity,
                info=info,
                state=state,
                device_path=device_path,
            )
        elif type=="tape":
            device = TapeDevice(
                serial=serial,
                name=name,
                kind=type,
                add_time=add_time,
                last_check_time=last_check_time,
                capacity=capacity,
                info=info,
                state=state,
                device_path=device_path,
            )
        else:
            raise ValueError(f"invalid kind: {type}")
        # 如果是DeviceState类型，则直接使用
        if isinstance(state, DeviceState):
            state = state.value
        # 如果是字符串，则需要转换为DeviceState类型
        elif state is None:
            state = DeviceState.HEALTHY
        elif state == "health":
            state = DeviceState.HEALTHY
        elif state == "danger":
            state = DeviceState.DANGER
        elif state == "fault":
            state = DeviceState.FAULT
        elif state == "no_longer_used":
            state = DeviceState.REMOVED
        elif state == "removed":
            state = DeviceState.REMOVED
        else:
            raise ValueError(f"invalid state: {state}")

        logger.info(f"成功构造设备: {device}")
        return device




        