import datetime
from apps.common.database.models import DeviceModel, DeviceState
from apps.common.database.session import session_scope
from apps.common.log import logger
from apps.domain.device import Device
from apps.infra.device.os_adapter import get_capacity, get_type, path2serial, serial2path

class SsdDevice(Device):
    def __init__(self, orm_model=None,device_path=None):
        super().__init__(orm_model,device_path)

    def check(self):
        pass

    def set(self, key, value):
        pass

    # @classmethod
    # def new_device(cls, *args, **kwargs):
    #     # 新建一个设备，并返回设备实例,还得写数据库

    #     serial = kwargs.get("serial")
    #     name = kwargs.get("name")
    #     kind = kwargs.get("kind")
    #     add_time = kwargs.get("add_time")
    #     last_check_time = kwargs.get("last_check_time")
    #     capacity = kwargs.get("capacity")
    #     state = kwargs.get("state")
    #     info = kwargs.get("info")
    #     path = kwargs.get("path")

    #     # 路径和序列号互验，保证序列号必须要有
    #     if path is None and serial is None:
    #         raise ValueError("path and serial must be provided")
    #     if path is not None and serial is None:
    #         serial = path2serial(path)
    #         if serial is None:
    #             raise ValueError("path is not a mounted device")
    #     if serial is not None and path is None:
    #         path = serial2path(serial)
    #         if path is None:
    #             logger.warning(f"this serial {serial} is not a mounted device, be careful that you entered a true serial number")
    #     if serial is not None and path is not None:
    #         if serial != path2serial(path):
    #             raise ValueError("serial and path do not match")
    #     # 名称默认处理
    #     if name is None:
    #         name = f"ssd-{serial[-8:]}"
    #     # 类型处理

    #     if kind is not None:
    #         if path is not None:
    #             path_kind = get_type(path)
    #             if path_kind is None:
    #                 raise ValueError(f"invalid path: {path}")
    #             if path_kind != kind:
    #                 logger.warning(f"the kind of {path} is not the same as the kind given, use auto get ")
    #                 kind = path_kind
    #     else:
    #         kind=get_type(path)

    #     # 时间处理
    #     if add_time is None:
    #         add_time = datetime.now()
    #     if last_check_time is None:
    #         # 设置成全0时间
    #         last_check_time = datetime.datetime(1, 1, 1, 0, 0, 0, 0)

    #     # 容量处理
    #     if capacity is None and path is not None:
    #         capacity = get_capacity(path)
    #     elif capacity is None and path is None:
    #         capacity = -1
    #         logger.warning(f"the capacity cannot be determined, please input it manually")
    #     elif capacity is not None and path is not None:
    #         path_capacity = get_capacity(path)
    #         if path_capacity != capacity:
    #             logger.warning(f"the capacity of {path} is not the same as the capacity given, use auto get ")
        
    #     if state is None:
    #         state = DeviceState.HEALTHY
    #     elif state == "health":
    #         state = DeviceState.HEALTHY
    #     elif state == "danger":
    #         state = DeviceState.DANGER
    #     elif state == "fault":
    #         state = DeviceState.FAULT
    #     elif state == "no_longer_used   ":
    #         state = DeviceState.NO_LONGER_USED
    #     elif state == "removed":
    #         state = DeviceState.REMOVED
    #     else:
    #         raise ValueError(f"invalid state: {state}")

    #     if info is None:
    #         info = ""
    #     orm_model = DeviceModel(\
    #         serial=serial, \
    #         name=name, \
    #         kind=kind, \
    #         add_time=add_time, \
    #         last_check_time=last_check_time, \
    #         capacity=capacity, \
    #         info=info, \
    #         state=state)
    #     device_path=serial2path(serial)

    #     with session_scope() as session:
    #         session.add(orm_model)
    #         session.commit()
    #     return cls(orm_model=orm_model, device_path=device_path)
