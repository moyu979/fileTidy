# CHECK: 待检查 - 领域层 Volume 实体基类 - 卷核心数据模型

import json
from abc import ABC
from datetime import datetime
from pathlib import Path

from domain.common.mixins import JsonSerializableMixin
from domain.storage.volume.enum import VolumeState


class Volume(ABC, JsonSerializableMixin):
    """卷抽象基类。

    定义卷（逻辑存储单元）的通用属性和方法。不同类型的卷继承此类并实现各自的逻辑。
    """

    # 子类注册表：file_system 字符串 → 具体变体类（由 __init_subclass__ 自动填充）
    _registry: dict[str, type["Volume"]] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        """子类定义时若声明 _type_key，则自动注册进 _registry。

        Args:
            **kwargs: 透传给父类 __init_subclass__。
        """
        super().__init_subclass__(**kwargs)
        key = cls.__dict__.get("_type_key")
        if key:
            Volume._registry[key] = cls

    @staticmethod
    def _resolve(file_system: str | None) -> type["Volume"]:
        """根据文件系统类型字符串查找对应的 Volume 子类。

        Args:
            file_system: 文件系统类型字符串，如 "ntfs", "exfat", "fat32", "ltfs"。

        Returns:
            对应的 Volume 子类；未匹配到或 file_system 为 None 时返回 Volume 基类。
        """
        if file_system is None:
            return Volume
        sub = Volume._registry.get(file_system)
        if sub is not None:
            return sub
        return Volume

    @classmethod
    def create(cls, *, serial: str, device_id: str = "", name: str = "",
               add_time=None, last_check_time=None, state=None, capacity=None,
               unique_mount_point=None, file_system: str | None = None,
               info=None, volume_path=None) -> "Volume":
        """通过显式字段创建对应子类的 Volume 实例（按 file_system 分派）。

        Args:
            serial: 卷序列号（必填）。
            device_id: 关联的设备序列号。
            name: 卷名称。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            state: 卷状态。
            capacity: 卷容量（字节）。
            unique_mount_point: 唯一挂载点标识。
            file_system: 文件系统类型。
            info: 附加信息。
            volume_path: 卷路径。

        Returns:
            对应子类的 Volume 实例。

        Raises:
            ValueError: serial 为空时抛出。
        """
        if not serial:
            raise ValueError("Volume.create: 'serial' is required")
        sub = Volume._resolve(file_system)
        return sub(serial=serial, device_id=device_id, name=name, add_time=add_time,
                   last_check_time=last_check_time, state=state, capacity=capacity,
                   unique_mount_point=unique_mount_point, file_system=file_system,
                   info=info, volume_path=volume_path)

    @classmethod
    def from_dict(cls, data: dict, volume_path: str | None = None) -> "Volume":
        """从字典数据重建对应子类的 Volume 实例。

        字段提取后委托给 create()，与 create 共用同一套分派/校验/构造逻辑。

        Args:
            data: 包含卷字段的字典，必须包含 "serial" 键。
            volume_path: 卷路径，若提供则覆盖 data 中的 volume_path。

        Returns:
            对应子类的 Volume 实例。

        Raises:
            ValueError: data 中缺少必需的 "serial" 字段时抛出（由 create 校验）。
        """
        return cls.create(
            serial=data.get("serial", ""),
            device_id=data.get("device_id", ""),
            name=data.get("name", ""),
            add_time=data.get("add_time"),
            last_check_time=data.get("last_check_time"),
            state=data.get("state"),
            capacity=data.get("capacity"),
            unique_mount_point=data.get("unique_mount_point"),
            file_system=data.get("file_system"),
            info=data.get("info"),
            volume_path=volume_path if volume_path is not None else data.get("volume_path"),
        )

    def __init__(
        self,
        serial: str,
        device_id: str,
        name: str,
        add_time: datetime,
        last_check_time: datetime,
        state: str | VolumeState,
        capacity: int | None,
        unique_mount_point: str | None,
        file_system: str,
        info: str | None,
        volume_path: str | None,
    ) -> None:
        """初始化卷实例。

        Args:
            serial: 卷序列号。
            device_id: 关联的设备序列号。
            name: 卷名称。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            state: 卷状态。
            capacity: 卷容量（字节）。
            unique_mount_point: 唯一挂载点标识。
            file_system: 文件系统类型（如 "ntfs", "exfat", "fat32", "ltfs"）。
            info: 附加信息。
            volume_path: 卷路径。
        """
        self.serial = serial
        self.device_id = device_id
        self.name = name
        self.add_time = add_time
        self.last_check_time = last_check_time
        self.state = state
        self.capacity = capacity
        self.unique_mount_point = unique_mount_point
        self.file_system = file_system
        self.info = info
        self.volume_path = volume_path

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
        """将卷转换为快照字典。

        Returns:
            包含卷所有字段的字典，时间字段会被格式化为 ISO 格式字符串。
        """
        return {
            "serial": self.serial,
            "device_id": self.device_id,
            "name": self.name,
            "add_time": self._ts(self.add_time),
            "last_check_time": self._ts(self.last_check_time),
            "state": self.state,
            "capacity": self.capacity,
            "unique_mount_point": self.unique_mount_point,
            "file_system": self.file_system,
            "info": self.info,
            "volume_path": self.volume_path,
        }

    @property
    def datas_path(self) -> str | None:
        """获取卷的数据目录路径（挂载点/datas）。

        Returns:
            数据目录路径字符串，volume_path 为 None 时返回 None。
        """
        if self.volume_path is None:
            return None
        return str(Path(self.volume_path) / "datas")

    @property
    def meta_path(self) -> str | None:
        """获取卷的元数据目录路径（挂载点/meta）。

        Returns:
            元数据目录路径字符串，volume_path 为 None 时返回 None。
        """
        if self.volume_path is None:
            return None
        return str(Path(self.volume_path) / "meta")
