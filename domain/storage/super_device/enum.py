# CHECK: 待检查 - 领域层 SuperDevice 枚举定义 - 超级设备类型/状态常量

from __future__ import annotations

import enum

from domain.common.menu import _Menu, _MenuOption


# ═══════════════════════════════════════════
#  超级设备状态
# ═══════════════════════════════════════════

class SuperDeviceState(enum.Enum):
    """超级设备状态枚举。

    定义超级设备可能处于的各种健康状态，包括降级（DEGRADING）状态。
    """
    UNKNOWN = "unknown" # 刚接入，尚未检测健康状态
    HEALTHY = "healthy" # 正常使用
    DANGER = "danger" # 危险，但暂时可用（有坏道等隐患）
    DEGRADING = "degrading" # 降级，部分子设备故障但仍在运行
    FAULT = "fault" # 故障，无法使用
    REMOVED = "removed" # 已移除（软删除，记录仍保留在数据库中）


# ═══════════════════════════════════════════
#  关联状态
# ═══════════════════════════════════════════

class RelationState(enum.Enum):
    """关联状态枚举。

    定义设备/卷与超级设备/超级卷之间的关联关系状态。
    """
    USING = "using"     # 正在使用
    UNUSED = "unused"   # 未使用，一般指代发生替换后之前的设备/卷


# ═══════════════════════════════════════════
#  菜单与说明类
# ═══════════════════════════════════════════

class SuperDeviceStateMenu(_Menu):
    """超级设备状态菜单。"""
    title = "超级设备状态"
    value_type = SuperDeviceState
    default = SuperDeviceState.UNKNOWN
    options = [
        _MenuOption("1", SuperDeviceState.UNKNOWN,   "UNKNOWN",  "未知（默认）"),
        _MenuOption("2", SuperDeviceState.HEALTHY,   "HEALTHY",  "健康"),
        _MenuOption("3", SuperDeviceState.DANGER,    "DANGER",   "危险"),
        _MenuOption("4", SuperDeviceState.DEGRADING, "DEGRADING","降级"),
        _MenuOption("5", SuperDeviceState.FAULT,     "FAULT",    "故障"),
        _MenuOption("6", SuperDeviceState.REMOVED,   "REMOVED",  "已移除"),
    ]


class SuperDeviceTypeMenu(_Menu):
    """超级设备类型菜单。"""
    title = "超级设备类型（与系统编号一致）"
    # value_type=None → from_code 直接返回类型字符串
    default = "single"
    options = [
        _MenuOption("1", "single", "单设备", "单个设备作为超级设备"),
        _MenuOption("2", "raidz",  "RAID-Z", "RAID-Z 冗余阵列"),
    ]