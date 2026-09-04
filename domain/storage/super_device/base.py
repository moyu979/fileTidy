# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 SuperDevice 实体基类 - 超级设备核心数据模型

import json
from abc import ABC
from datetime import datetime

from domain.common.mixins import JsonSerializableMixin
from domain.storage.super_device.enum import SuperDeviceState


class SuperDevice(ABC, JsonSerializableMixin):
    """超级设备抽象基类。

    定义由多个物理设备组合而成的逻辑设备（如 RAID-Z、单设备超级设备等）的通用属性和方法。
    """

    # 子类注册表：sdtype 字符串 → 具体变体类（由 __init_subclass__ 自动填充）
    _registry: dict[str, type["SuperDevice"]] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        """子类定义时若声明 _type_key，则自动注册进 _registry。

        Args:
            **kwargs: 透传给父类 __init_subclass__。
        """
        super().__init_subclass__(**kwargs)
        key = cls.__dict__.get("_type_key")
        if key:
            SuperDevice._registry[key] = cls

    @staticmethod
    def _resolve(sdtype: str | None) -> type["SuperDevice"]:
        """根据超级设备类型字符串查找对应的 SuperDevice 子类。

        Args:
            sdtype: 超级设备类型字符串，如 "single", "raidz"。

        Returns:
            对应的 SuperDevice 子类；未匹配到或 sdtype 为 None 时返回 SuperDevice 基类。
        """
        if sdtype is None:
            return SuperDevice
        sub = SuperDevice._registry.get(sdtype)
        if sub is not None:
            return sub
        return SuperDevice

    @classmethod
    def create(cls, *, serial: str, name: str = "", sdtype: str | None = None,
               need_all_devices_online: bool = False, add_time=None, last_check_time=None,
               state=None, capacity=None, info=None, devices: list[str] | None = None) -> "SuperDevice":
        """通过显式字段创建对应子类的 SuperDevice 实例（按 sdtype 分派）。

        Args:
            serial: 超级设备序列号（必填）。
            name: 超级设备名称，默认空字符串。
            sdtype: 超级设备类型，默认 None。
            need_all_devices_online: 是否需要所有子设备在线。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            state: 超级设备状态。
            capacity: 超级设备总容量（字节）。
            info: 附加信息。
            devices: 子设备序列号列表。

        Returns:
            对应子类的 SuperDevice 实例。

        Raises:
            ValueError: serial 为空时抛出。
        """
        if not serial:
            raise ValueError("SuperDevice.create: 'serial' is required")
        sub = SuperDevice._resolve(sdtype)
        return sub(
            serial=serial, name=name, sdtype=sdtype,
            need_all_devices_online=need_all_devices_online,
            add_time=add_time, last_check_time=last_check_time,
            state=state, capacity=capacity, info=info, devices=devices or [],
        )

    @classmethod
    def from_dict(cls, data: dict) -> "SuperDevice":
        """从字典数据重建对应子类的 SuperDevice 实例。

        字段提取后委托给 create()，与 create 共用同一套分派/校验/构造逻辑。

        Args:
            data: 包含超级设备字段的字典，必须包含 "serial" 键。

        Returns:
            对应子类的 SuperDevice 实例。

        Raises:
            ValueError: data 中缺少必需的 "serial" 字段时抛出（由 create 校验）。
        """
        return cls.create(
            serial=data.get("serial", ""),
            name=data.get("name", ""),
            sdtype=data.get("type"),
            need_all_devices_online=data.get("need_all_devices_online", False),
            add_time=data.get("add_time"),
            last_check_time=data.get("last_check_time"),
            state=data.get("state"),
            capacity=data.get("capacity"),
            info=data.get("info"),
            devices=data.get("devices", []),
        )

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
    ) -> None:
        """初始化超级设备实例。

        Args:
            serial: 超级设备序列号。
            name: 超级设备名称。
            sdtype: 超级设备类型（如 "single", "raidz"）。
            need_all_devices_online: 是否需要所有子设备在线才能工作。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            state: 超级设备状态。
            capacity: 超级设备总容量（字节）。
            info: 附加信息。
            devices: 组成该超级设备的子设备序列号列表。
        """
        self.serial = serial
        self.name = name
        self.sdtype = sdtype
        self.need_all_devices_online = need_all_devices_online
        self.add_time = add_time
        self.last_check_time = last_check_time
        self.state = state
        self.capacity = capacity
        self.info = info
        self.devices = devices

    def _parse_info(self) -> dict:
        """解析 info（JSON 文本）为字典。

        Returns:
            解析后的 dict；info 为空或非法 JSON 时返回空字典 {}。
        """
        if not self.info:
            return {}
        try:
            data = json.loads(self.info)
        except (json.JSONDecodeError, TypeError):
            return {}
        return data if isinstance(data, dict) else {}

    def to_snapshot(self) -> dict:
        """将超级设备转换为快照字典。

        Returns:
            包含超级设备所有字段的字典，时间字段会被格式化为 ISO 格式字符串。
        """
        return {
            "serial": self.serial,
            "name": self.name,
            "type": self.sdtype,
            "need_all_devices_online": self.need_all_devices_online,
            "add_time": self._ts(self.add_time),
            "last_check_time": self._ts(self.last_check_time),
            "state": self.state,
            "capacity": self.capacity,
            "info": self.info,
            "devices": list(self.devices),
        }
