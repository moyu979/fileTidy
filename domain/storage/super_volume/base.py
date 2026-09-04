# CHECK: 待检查 - 领域层 SuperVolume 实体基类 - 超级卷核心数据模型

from __future__ import annotations

import json
from abc import ABC
from datetime import datetime

from domain.common.mixins import JsonSerializableMixin
from domain.storage.super_volume.enum import SuperVolumeState


class SuperVolume(ABC, JsonSerializableMixin):
    """超级卷抽象基类。

    定义由多个卷组合而成的逻辑存储单元（如复制、SnapRAID RAID5 等）的通用属性和方法。
    """

    # 子类注册表：svtype 字符串 → 具体变体类（由 __init_subclass__ 自动填充）
    _registry: dict[str, type["SuperVolume"]] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        """子类定义时若声明 _type_key，则自动注册进 _registry。

        Args:
            **kwargs: 透传给父类 __init_subclass__。
        """
        super().__init_subclass__(**kwargs)
        key = cls.__dict__.get("_type_key")
        if key:
            SuperVolume._registry[key] = cls

    @staticmethod
    def _resolve(svtype: str | None) -> type["SuperVolume"]:
        """根据超级卷类型字符串查找对应的 SuperVolume 子类。

        Args:
            svtype: 超级卷类型字符串，如 "copy", "snapraid_raid5"。

        Returns:
            对应的 SuperVolume 子类；未匹配到或 svtype 为 None 时返回 SuperVolume 基类。
        """
        if svtype is None:
            return SuperVolume
        sub = SuperVolume._registry.get(svtype)
        if sub is not None:
            return sub
        return SuperVolume

    @classmethod
    def create(
        cls,
        *,
        serial: str,
        name: str = "",
        svtype: str | None = None,
        method: str = "",
        add_time=None,
        last_check_time=None,
        state=None,
        info=None,
        volumes: list[str] | None = None,
    ) -> "SuperVolume":
        """通过显式字段创建对应子类的 SuperVolume 实例（按 svtype 分派）。

        Args:
            serial: 超级卷序列号（必填）。
            name: 超级卷名称，默认空字符串。
            svtype: 超级卷类型，默认 None。
            method: 组合方法描述。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            state: 超级卷状态。
            info: 附加信息。
            volumes: 子卷序列号列表。

        Returns:
            对应子类的 SuperVolume 实例。

        Raises:
            ValueError: serial 为空时抛出。
        """
        if not serial:
            raise ValueError("SuperVolume.create: 'serial' is required")
        sub = SuperVolume._resolve(svtype)
        return sub(
            serial=serial,
            name=name,
            svtype=svtype,
            method=method,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            info=info,
            volumes=volumes or [],
        )

    @classmethod
    def from_dict(cls, data: dict) -> "SuperVolume":
        """从字典数据重建对应子类的 SuperVolume 实例。

        字段提取后委托给 create()，与 create 共用同一套分派/校验/构造逻辑。

        Args:
            data: 包含超级卷字段的字典，必须包含 "serial" 键。

        Returns:
            对应子类的 SuperVolume 实例。

        Raises:
            ValueError: data 中缺少必需的 "serial" 字段时抛出（由 create 校验）。
        """
        return cls.create(
            serial=data.get("serial", ""),
            name=data.get("name", ""),
            svtype=data.get("type"),
            method=data.get("method", ""),
            add_time=data.get("add_time"),
            last_check_time=data.get("last_check_time"),
            state=data.get("state"),
            info=data.get("info"),
            volumes=data.get("volumes", []),
        )

    def __init__(
        self,
        serial: str,
        name: str,
        svtype: str,
        method: str,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperVolumeState,
        info: str,
        volumes: list[str],
    ) -> None:
        """初始化超级卷实例。

        Args:
            serial: 超级卷序列号。
            name: 超级卷名称。
            svtype: 超级卷类型（如 "copy", "snapraid_raid5"）。
            method: 组合方法描述。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            state: 超级卷状态。
            info: 附加信息。
            volumes: 组成该超级卷的子卷序列号列表。
        """
        self.serial = serial
        self.name = name
        self.svtype = svtype
        self.method = method
        self.add_time = add_time
        self.last_check_time = last_check_time
        self.state = state
        self.info = info
        self.volumes = volumes

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
        """将超级卷转换为快照字典。

        Returns:
            包含超级卷所有字段的字典，时间字段会被格式化为 ISO 格式字符串。
        """
        return {
            "serial": self.serial,
            "name": self.name,
            "type": self.svtype,
            "method": self.method,
            "add_time": self._ts(self.add_time),
            "last_check_time": self._ts(self.last_check_time),
            "state": self.state,
            "info": self.info,
            "volumes": list(self.volumes),
        }
