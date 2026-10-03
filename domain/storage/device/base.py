# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: ai生成，待检查 - 领域层 Device 实体基类 - 设备核心数据模型

"""
设备层抽象，用于管理硬件设备，主要用于提供操作硬件设备的抽象,包括：
- 硬盘
- 磁带
    - lto5
    - lto6
- TF卡
- 其他硬件设备

主要用于提供操作硬件设备的抽象
本文件是一个抽象层，具体的实现中drivers里 
"""
from abc import ABC

from domain.common.json_utils import parse_json_object
from domain.common.mixins import JsonSerializableMixin
from domain.storage.device.enum import DeviceState


class Device(ABC, JsonSerializableMixin):
    # 子类注册表：type 字符串 → 具体变体类（由 __init_subclass__ 自动填充）
    _registry: dict[str, type["Device"]] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        """子类定义时若声明 _type_key，则自动注册进 _registry。

        Args:
            **kwargs: 透传给父类 __init_subclass__。
        """
        super().__init_subclass__(**kwargs)
        key = cls.__dict__.get("_type_key")
        if key:
            Device._registry[key] = cls

    @staticmethod
    def _resolve(dtype: str | None) -> type["Device"]:
        """根据设备类型字符串查找对应的 Device 子类。

        Args:
            dtype: 设备类型字符串，如 "hdd", "ssd", "tape", "tf_sd_card"。

        Returns:
            对应的 Device 子类；未匹配到或 dtype 为 None 时返回 Device 基类。

        Note:
            兼容旧数据：早期磁带把代次拼在 type 里（如 "tape-lto5"），仍解析为 TapeDevice。
        """
        if dtype is None:
            return Device
        sub = Device._registry.get(dtype)
        if sub is not None:
            return sub
        if isinstance(dtype, str) and dtype.startswith("tape"):
            return Device._registry.get("tape", Device)
        return Device

    @classmethod
    def create(cls, *, serial: str, name: str = "", dtype: str | None = None,
               add_time=None, last_check_time=None, state=None, capacity=None,
               info=None, device_path=None) -> "Device":
        """通过显式字段创建对应子类的 Device 实例（按 dtype 分派）。

        Args:
            serial: 设备序列号（必填）。
            name: 设备名称，默认空字符串。
            dtype: 设备类型，默认 None。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            state: 设备状态。
            capacity: 设备容量（字节）。
            info: 附加信息。
            device_path: 挂载路径。

        Returns:
            对应子类的 Device 实例。

        Raises:
            ValueError: serial 为空时抛出。
        """
        if not serial:
            raise ValueError("Device.create: 'serial' is required")
        sub = Device._resolve(dtype)
        return sub(serial=serial, name=name, dtype=dtype, add_time=add_time,
                   last_check_time=last_check_time, state=state, capacity=capacity,
                   info=info, device_path=device_path)

    @classmethod
    def from_dict(cls, data: dict, device_path: str | None = None) -> "Device":
        """从字典数据重建对应子类的 Device 实例。

        字段提取后委托给 create()，与 create 共用同一套分派/校验/构造逻辑。

        Args:
            data: 包含设备字段的字典，必须包含 "serial" 键。
            device_path: 设备挂载路径，若提供则覆盖 data 中的 device_path。

        Returns:
            对应子类的 Device 实例。

        Raises:
            ValueError: data 中缺少必需的 "serial" 字段时抛出（由 create 校验）。
        """
        return cls.create(
            serial=data.get("serial", ""),
            name=data.get("name", ""),
            dtype=data.get("dtype"),
            add_time=data.get("add_time"),
            last_check_time=data.get("last_check_time"),
            state=data.get("state"),
            capacity=data.get("capacity"),
            info=data.get("info"),
            device_path=device_path if device_path is not None else data.get("device_path"),
        )

    def __init__(self, 
    serial: str,
    name: str,
    dtype: str|None,
    add_time,
    last_check_time,
    state: str|None,
    capacity: int|None,
    info: str|None,
    device_path: str|None=None,
    ) -> None:
        """初始化设备实例。

        Args:
            serial: 设备序列号，唯一标识一台设备。
            name: 设备名称。
            dtype: 设备类型（如 "hdd", "ssd", "tape", "tf_sd_card" 等）。
            add_time: 设备添加时间。
            last_check_time: 设备最后一次健康检查时间。
            state: 设备状态（如 "healthy", "fault" 等）。
            capacity: 设备存储容量（字节）。
            info: 设备的其他附加信息（JSON 字符串）。
            device_path: 设备挂载路径，None 表示未挂载。
        """
        self.serial = serial  # 设备的序列号
        self.name = name  # 设备的名称
        self.dtype = dtype  # 设备的类型
        self.add_time = add_time  # 设备的添加时间
        self.last_check_time = last_check_time  # 设备的最后一次检查时间
        self.state = state  # 设备的状态
        self.capacity = capacity  # 设备的容量
        self.info = info  # 设备的其他信息
        self.device_path = device_path  # 设备的实际挂载路径，如果是None，说明这个设备没挂载
        

    def _parse_info(self) -> dict:
        """解析 info（JSON 文本）为字典（薄封装，逻辑见 parse_json_object）。

        Returns:
            解析后的 dict；info 为空 / 非法 JSON / 非对象 JSON 时返回空字典 {}。
        """
        return parse_json_object(self.info)

    def is_removed(self) -> bool:
        """当前 state 是否为 REMOVED（软删除）。

        兼容枚举成员、值字符串（"removed"）与名称字符串（"REMOVED"）三种形态：
        实体 state 正常是 DeviceState 成员，但外部（脚本 / 测试替身）可能直接塞字符串。

        Returns:
            True 表示处于 REMOVED 状态。
        """
        if self.state is DeviceState.REMOVED:
            return True
        if isinstance(self.state, str):
            return self.state in (DeviceState.REMOVED.value, DeviceState.REMOVED.name)
        return False

    def to_snapshot(self) -> dict:
        """将设备转换为快照字典。

        Returns:
            包含设备所有字段的字典，时间字段会被格式化为 ISO 格式字符串。
        """
        return {
            "serial": self.serial,
            "name": self.name,
            "dtype": self.dtype,
            "add_time": self._ts(self.add_time),
            "last_check_time": self._ts(self.last_check_time),
            "state": self.state,
            "capacity": self.capacity,
            "info": self.info,
            "device_path": self.device_path,
        }
