# CHECK: 待检查 - 领域层 RAIDZ 变体 - RAIDZ 超级设备实现

import datetime
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState


class RaidzSuperDevice(SuperDevice):
    """RAID-Z 超级设备类。

    继承自 SuperDevice 基类，代表由多个硬盘组成的 RAID-Z 冗余阵列。
    """
    _type_key = "raidz"

    # TODO(P3): 当前仅透传构造函数，后续可添加 RAID-Z 的校验/恢复等特有逻辑
    def __init__(self,
        serial: str,
        name: str,
        sdtype: str,
        need_all_devices_online: bool,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperDeviceState,
        capacity: int,
        info: str,
        devices: list[str],
    ):
        """初始化 RAID-Z 超级设备实例。

        Args:
            serial: 超级设备序列号。
            name: 超级设备名称。
            sdtype: 超级设备类型。
            need_all_devices_online: 是否需要所有子设备在线。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            state: 超级设备状态。
            capacity: 总容量（字节）。
            info: 附加信息。
            devices: 子设备序列号列表。
        """
        super().__init__(serial, name, sdtype, need_all_devices_online,
                         add_time, last_check_time, state, capacity, info, devices)