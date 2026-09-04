# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: ai生成，待检查 - 领域层 Device 领域事件 - 设备相关事件定义

from __future__ import annotations

from domain.storage.device.base import Device


class DeviceRegistered:
    """设备注册事件。

    当新设备注册到系统时触发。
    """
    def __init__(self, device: Device):
        """
        Args:
            device: 被注册的设备实例，其快照将被保存到事件中。
        """
        snapshot = device.to_snapshot()
        self.serial = snapshot["serial"]  # 顶层冗余身份字段，便于按 serial 筛日志
        self.device = snapshot            # 完整快照（聚合）


class DeviceFieldUpdated:
    """设备普通字段更新事件（name / type / state / capacity）。

    注意：info 的变更请使用 DeviceInfo* 系列事件，不要用本事件记 field="info"。
    """
    def __init__(self, serial: str, field: str, old_value, new_value):
        """
        Args:
            serial: 被更新设备的序列号。
            field: 被更新的字段名。
            old_value: 字段原值。
            new_value: 字段新值。
        """
        self.serial = serial
        self.field = field
        self.old_value = old_value
        self.new_value = new_value


class DeviceInfoSet:
    """设备 info 字段全量替换事件。"""
    def __init__(self, serial: str, old_info: dict, new_info: dict):
        """
        Args:
            serial: 被更新设备的序列号。
            old_info: 替换前的 info 字典。
            new_info: 替换后的 info 字典。
        """
        self.serial = serial
        self.old_info = old_info
        self.new_info = new_info


class DeviceInfoChanged:
    """设备 info 单键变更事件（serial-op-key-old-new 五元组记录）。

    只记录"一个 key 的一次增删改"，本身不包含差异计算逻辑——由上层（应用层）
    判断要发哪个 op、并逐键构造本事件。一次涉及多个 key 的变更建议直接用
    DeviceInfoSet（全量替换）记录，而不是拆成多条本事件。

    op 取值：
      - op="add"     新增键（new 有值，old 为 None）
      - op="remove"  删除键（old 有值，new 为 None）
      - op="replace" 修改已有键（old 与 new 都有值）

    显式 op 避免用"old/new 为空"推断操作类型——info 的值本身可能是 None 或
    空字符串，靠空值推断会误判（如 {"a": None} → {"a": 1} 会被当成新增）。
    """
    def __init__(self, serial: str, op: str, key: str, old, new):
        """
        Args:
            serial: 被更新设备的序列号。
            op: 操作类型，add / remove / replace 之一。
            key: 发生变化的 info 键名。
            old: 变更前的值（op="add" 时为 None）。
            new: 变更后的值（op="remove" 时为 None）。
        """
        self.serial = serial
        self.op = op
        self.key = key
        self.old = old
        self.new = new


class DeviceSerialChanged:
    """设备序列号变更事件。"""
    def __init__(self, old_serial: str, new_serial: str):
        """
        Args:
            old_serial: 原设备序列号。
            new_serial: 新设备序列号。
        """
        self.old_serial = old_serial
        self.new_serial = new_serial


class DeviceRemoved:
    """设备移除（软删除）事件。"""
    def __init__(self, serial: str):
        """
        Args:
            serial: 被移除（标记 REMOVED）设备的序列号。
        """
        self.serial = serial