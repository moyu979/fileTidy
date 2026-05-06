from domain.storage.device.base import Device


class SuperDevice(ABC):
    def __init__(self,
        name: str,
        type: str,
        info: str,
        need_all_devices_online: bool,
        devices: list[Device],
    ) -> None:
        # 超级设备id
        super_device_id = None
        # 超级设备名称
        self.name = name
        # 超级设备类型 如：磁带卷、硬盘卷、RAID5卷等
        self.type = type
        # 是否需要全部设备同时上线
        need_all_devices_online = need_all_devices_online
        # 登记时间
        self.add_time = datetime.now()
        # 最后一次检查时间
        self.last_check_time = None
        # 超级设备状态，如健康、故障等
        self.state = SuperDeviceState.HEALTHY
        # 超级设备容量（字节）
        self.capacity = 0
        # 超级设备其他信息
        self.info = info