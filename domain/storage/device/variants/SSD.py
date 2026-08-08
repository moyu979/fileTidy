# CHECK: ai生成，待检查 - 领域层 SSD 变体 - 固态硬盘设备实现

import datetime

from domain.storage.device.base import Device
from domain.storage.device.enum import DeviceFormFactor, DeviceInterface


class SsdDevice(Device):
    """固态硬盘（SSD）设备类。

    继承自 Device 基类，代表物理固态硬盘设备。
    """
    _type_key = "ssd"

    # TODO(P3): check() 和 set() 目前是空实现，需要实现真正的固态硬盘健康检查和属性设置逻辑
    def __init__(self, 
    serial: str,
    name: str,
    dtype: str|None,
    add_time,
    last_check_time,
    capacity: int|None,
    info: str|None,
    state: str|None,
    device_path: str|None,
    ) -> None:
        """初始化 SSD 设备实例。

        Args:
            serial: 设备序列号。
            name: 设备名称。
            dtype: 设备类型。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            capacity: 设备容量（字节）。
            info: 附加信息。
            state: 设备状态。
            device_path: 挂载路径。
        """
        super().__init__(serial, 
            name, 
            dtype, 
            add_time, 
            last_check_time, 
            capacity, 
            info, 
            state,
            device_path)

    def get_interface(self) -> DeviceInterface | None:
        """获取磁盘接口。

        从 info（JSON）中的 "interface" 键读取，并校验为合法的 DeviceInterface。

        Returns:
            DeviceInterface 枚举；info 中缺失或值非法时返回 None。
        """
        iface = self._parse_info().get("interface")
        if not iface:
            return None
        try:
            return DeviceInterface(iface)
        except ValueError:
            return None

    def get_form_factor(self) -> DeviceFormFactor | None:
        """获取磁盘物理尺寸/形态。

        从 info（JSON）中的 "form_factor" 键读取，并校验为合法的 DeviceFormFactor。

        Returns:
            DeviceFormFactor 枚举；info 中缺失或值非法时返回 None。
        """
        ff = self._parse_info().get("form_factor")
        if not ff:
            return None
        try:
            return DeviceFormFactor(ff)
        except ValueError:
            return None

    def check(self):
        """执行固态硬盘健康检查。

        Returns:
            None（当前为占位实现，待实现真正的健康检查）。
        """
        pass

    def set(self, key, value):
        """设置固态硬盘属性。

        Args:
            key: 属性键名。
            value: 属性值。

        Returns:
            None（当前为占位实现，待实现真正的属性设置逻辑）。
        """
        pass