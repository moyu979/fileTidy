# CHECK: 待检查 - 领域层 SuperVolume 领域事件 - 超级卷相关事件定义

from __future__ import annotations

from domain.storage.super_volume.base import SuperVolume


class SuperVolumeRegistered:
    """超级卷注册事件。

    当新超级卷注册到系统时触发。
    """
    def __init__(self, super_volume: SuperVolume):
        """
        Args:
            super_volume: 被注册的超级卷实例。
        """
        snapshot = super_volume.to_snapshot()
        self.serial = snapshot["serial"]  # 顶层冗余身份字段，便于按 serial 筛日志
        self.super_volume = snapshot      # 完整快照（聚合）


class SuperVolumeFieldUpdated:
    """超级卷普通字段更新事件（name / svtype / state / method 等）。

    注意：info 的变更请使用 SuperVolumeInfo* 系列事件，不要用本事件记 field="info"。
    """
    def __init__(self, serial: str, field: str, old_value, new_value):
        """
        Args:
            serial: 被更新超级卷的序列号。
            field: 被更新的字段名。
            old_value: 字段原值。
            new_value: 字段新值。
        """
        self.serial = serial
        self.field = field
        self.old_value = old_value
        self.new_value = new_value


class SuperVolumeInfoSet:
    """超级卷 info 字段全量替换事件。"""
    def __init__(self, serial: str, old_info: dict, new_info: dict):
        """
        Args:
            serial: 被更新超级卷的序列号。
            old_info: 替换前的 info 字典。
            new_info: 替换后的 info 字典。
        """
        self.serial = serial
        self.old_info = old_info
        self.new_info = new_info


class SuperVolumeInfoChanged:
    """超级卷 info 单键变更事件（serial-op-key-old-new 五元组记录）。

    只记录"一个 key 的一次增删改"，本身不包含差异计算逻辑——由上层（应用层）
    判断要发哪个 op、并逐键构造本事件。一次涉及多个 key 的变更建议直接用
    SuperVolumeInfoSet（全量替换）记录，而不是拆成多条本事件。

    op 取值：
      - op="add"     新增键（new 有值，old 为 None）
      - op="remove"  删除键（old 有值，new 为 None）
      - op="replace" 修改已有键（old 与 new 都有值）
    """
    def __init__(self, serial: str, op: str, key: str, old, new):
        """
        Args:
            serial: 被更新超级卷的序列号。
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


class SuperVolumeSerialChanged:
    """超级卷序列号变更事件。"""
    def __init__(self, old_serial: str, new_serial: str):
        """
        Args:
            old_serial: 原超级卷序列号。
            new_serial: 新超级卷序列号。
        """
        self.old_serial = old_serial
        self.new_serial = new_serial


class VolumesAddedToSuperVolume:
    """卷被添加到超级卷时触发的事件。"""

    def __init__(self, super_volume_serial: str, volume_ids: list[str]) -> None:
        """
        Args:
            super_volume_serial: 目标超级卷序列号。
            volume_ids: 被添加的子卷序列号列表。
        """
        self.super_volume_serial = super_volume_serial
        self.volume_ids = list(volume_ids)

    def to_snapshot(self) -> dict:
        """将事件转换为快照字典。

        Returns:
            包含超级卷序列号和子卷 ID 列表的字典。
        """
        return {
            "super_volume_serial": self.super_volume_serial,
            "volume_ids": list(self.volume_ids),
        }


class VolumesRemovedFromSuperVolume:
    """卷从超级卷移除时触发的事件。"""

    def __init__(self, super_volume_serial: str, volume_ids: list[str]) -> None:
        """
        Args:
            super_volume_serial: 目标超级卷序列号。
            volume_ids: 被移除的子卷序列号列表。
        """
        self.super_volume_serial = super_volume_serial
        self.volume_ids = list(volume_ids)

    def to_snapshot(self) -> dict:
        """将事件转换为快照字典。

        Returns:
            包含超级卷序列号和子卷 ID 列表的字典。
        """
        return {
            "super_volume_serial": self.super_volume_serial,
            "volume_ids": list(self.volume_ids),
        }


class SuperVolumeRemoved:
    """超级卷移除（软删除）事件。"""
    def __init__(self, serial: str):
        """
        Args:
            serial: 被移除（标记 REMOVED）超级卷的序列号。
        """
        self.serial = serial
