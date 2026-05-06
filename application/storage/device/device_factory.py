from datetime import datetime
import logging

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
from infra.system.storage.device.is_disk import is_disk

logger = logging.getLogger(__name__)

class device_factory:
    def __init__(self) -> None:
        pass

    @staticmethod
    def load_device(
        serial: str | None,
        device_path: str | None,
        session_factory,
    ) -> Device | None:
        if serial is None and device_path is not None:
            serial = get_serial(device_path)
        if serial is None:
            raise ValueError("serial and device_path are both None")

        with session_scope(session_factory) as session:
            row = (
                session.query(DeviceModel)
                .filter(DeviceModel.serial == serial)
                .first()
            )
            if row is None:
                return None
            # 在 Session 仍打开时取出标量，避免关闭会话后 DetachedInstanceError
            d_serial = row.serial
            d_name = row.name
            d_type = row.type
            d_add_time = row.add_time
            d_last_check_time = row.last_check_time
            d_capacity = row.capacity
            d_info = row.info
            d_state = row.state

        if d_type == "ssd":
            return SsdDevice(
                serial=d_serial,
                name=d_name,
                type=d_type,
                add_time=d_add_time,
                last_check_time=d_last_check_time,
                capacity=d_capacity,
                info=d_info,
                state=d_state,
                device_path=device_path,
            )
        if d_type == "hdd":
            return HddDevice(
                serial=d_serial,
                name=d_name,
                type=d_type,
                add_time=d_add_time,
                last_check_time=d_last_check_time,
                capacity=d_capacity,
                info=d_info,
                state=d_state,
                device_path=device_path,
            )
        if d_type == "tf_sd_card":
            return TfSdCardDevice(
                serial=d_serial,
                name=d_name,
                type=d_type,
                add_time=d_add_time,
                last_check_time=d_last_check_time,
                capacity=d_capacity,
                info=d_info,
                state=d_state,
                device_path=device_path,
            )
        if d_type == "tape":
            return TapeDevice(
                serial=d_serial,
                name=d_name,
                type=d_type,
                add_time=d_add_time,
                last_check_time=d_last_check_time,
                capacity=d_capacity,
                info=d_info,
                state=d_state,
                device_path=device_path,
            )
        if d_type == "any":
            return Device(
                serial=d_serial,
                name=d_name,
                type=d_type,
                add_time=d_add_time,
                last_check_time=d_last_check_time,
                capacity=d_capacity,
                info=d_info,
                state=d_state,
                device_path=device_path,
            )
        raise ValueError(f"invalid type: {d_type}")

    # @staticmethod
    # def new_device(
    #     serial: str,
    #     name: str,
    #     type: str,
    #     add_time,
    #     last_check_time,
    #     capacity: int,
    #     info: str,
    #     state: str,
    #     device_path: str,
    # ) -> Device:
    #     device=None
    #     if type=="ssd":
    #         device = SsdDevice(
    #             serial=serial,
    #             name=name,
    #             type=type,
    #             add_time=add_time,
    #             last_check_time=last_check_time,
    #             capacity=capacity,
    #             info=info,
    #             state=state,
    #             device_path=device_path,
    #         )
    #     elif type=="hdd":
    #         device = HddDevice(
    #             serial=serial,
    #             name=name,
    #             type=type,
    #             add_time=add_time,
    #             last_check_time=last_check_time,
    #             capacity=capacity,
    #             info=info,
    #             state=state,
    #             device_path=device_path,
    #         )
    #     elif type=="tf_sd_card":
    #         device = TfSdCardDevice(
    #             serial=serial,
    #             name=name,
    #             kind=type,
    #             add_time=add_time,
    #             last_check_time=last_check_time,
    #             capacity=capacity,
    #             info=info,
    #             state=state,
    #             device_path=device_path,
    #         )
    #     elif type=="tape":
    #         device = TapeDevice(
    #             serial=serial,
    #             name=name,
    #             kind=type,
    #             add_time=add_time,
    #             last_check_time=last_check_time,
    #             capacity=capacity,
    #             info=info,
    #             state=state,
    #             device_path=device_path,
    #         )
    #     else:
    #         raise ValueError(f"invalid kind: {type}")

    # 将数据记录到数据库    
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
        if device_path is None:
            if serial is None:
                raise ValueError("serial and device_path are both None")
            else:
                device_path = get_path(serial)
        # 如果路径不为空，则需要校验路径给出的序列号与实际的序列号是否一致
        elif device_path is not None:
            if serial is None:
                serial = get_serial(device_path)
            else:
                if serial != get_serial(device_path):
                    raise ValueError(f"the serial of {device_path} is not the same as the serial given")
        # 校验按路径获得的信息与给定的是否一致
        if device_path is not None:
            # 校验路径的类型是否与给定的类型一致
            kind_from_path=get_type(device_path)
            if type==None or type==kind_from_path:
                type=kind_from_path
            else:
                raise ValueError(f"the kind of {device_path} is not the same as the kind given, use auto get ")
            # 检查路径确实是一个device的挂载点
            if not is_disk(device_path):
                raise ValueError(f"the path {device_path} is not a device's mount point")
                
            # 校验容量与给定的是否一致
            capacity_from_path = get_capacity(device_path)
            if capacity==None or capacity==capacity_from_path:
                capacity=capacity_from_path
            else:
                raise ValueError(f"the capacity of {device_path} is not the same as the capacity given, please input it manually")  
                
        if add_time is None:
            add_time = datetime.now()
        if last_check_time is None:
            last_check_time = datetime.now()
            
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

        if state is None:
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




        