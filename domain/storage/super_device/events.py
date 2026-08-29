# CHECK: 待检查 - 领域层 SuperDevice 领域事件 - 超级设备相关事件定义
# TODO 思考一下开始操作的时间要不要加
from __future__ import annotations

from domain.storage.super_device.base import SuperDevice


class SuperDeviceRegistered:
    """超级设备注册事件。

    当新超级设备注册到系统时触发。
    """
    def __init__(self, super_device: SuperDevice):
        """
        Args:
            super_device: 被注册的超级设备实例。
        """
        snapshot = super_device.to_snapshot()
        self.serial = snapshot["serial"]  # 顶层冗余身份字段，便于按 serial 筛日志
        self.device = snapshot            # 完整快照（聚合）


class SuperDeviceFieldUpdated:
    """超级设备普通字段更新事件（name / sdtype / state / capacity / need_all_devices_online）。

    注意：info 的变更请使用 SuperDeviceInfo* 系列事件，不要用本事件记 field="info"。
    """
    def __init__(self, serial: str, field: str, old_value, new_value):
        """
        Args:
            serial: 被更新超级设备的序列号。
            field: 被更新的字段名。
            old_value: 字段原值。
            new_value: 字段新值。
        """
        self.serial = serial
        self.field = field
        self.old_value = old_value
        self.new_value = new_value


class SuperDeviceInfoSet:
    """超级设备 info 字段全量替换事件。"""
    def __init__(self, serial: str, old_info: dict, new_info: dict):
        """
        Args:
            serial: 被更新超级设备的序列号。
            old_info: 替换前的 info 字典。
            new_info: 替换后的 info 字典。
        """
        self.serial = serial
        self.old_info = old_info
        self.new_info = new_info


class SuperDeviceInfoChanged:
    """超级设备 info 单键变更事件（serial-op-key-old-new 五元组记录）。

    只记录"一个 key 的一次增删改"，本身不包含差异计算逻辑——由上层（应用层）
    判断要发哪个 op、并逐键构造本事件。一次涉及多个 key 的变更建议直接用
    SuperDeviceInfoSet（全量替换）记录，而不是拆成多条本事件。

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
            serial: 被更新超级设备的序列号。
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


class SuperDeviceSerialChanged:
    """超级设备序列号变更事件。"""
    def __init__(self, old_serial: str, new_serial: str):
        """
        Args:
            old_serial: 原超级设备序列号。
            new_serial: 新超级设备序列号。
        """
        self.old_serial = old_serial
        self.new_serial = new_serial


class SuperDeviceDeviceChanged:
    """超级设备的子设备变更事件（新增 / 移除 / 替换）。

    - 新增设备: old=None, new=<设备serial>
    - 移除设备: old=<设备serial>, new=None
    - 替换设备: old=<旧设备serial>, new=<新设备serial>
    """
    def __init__(self, super_device_serial: str, old: str | None, new: str | None):
        """
        Args:
            super_device_serial: 发生变更的超级设备序列号。
            old: 变更前的设备序列号（新增时为 None）。
            new: 变更后的设备序列号（移除时为 None）。
        """
        self.super_device_serial = super_device_serial
        self.old = old
        self.new = new


class SuperDeviceRemoved:
    """超级设备移除（软删除）事件。"""
    def __init__(self, serial: str):
        """
        Args:
            serial: 被移除（标记 REMOVED）超级设备的序列号。
        """
        self.serial = serial