# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
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
    # 已移除（软删除，记录仍保留在数据库中）。
    # **可逆**：用 `revive_super_device` 复活 —— 原地 UPDATE（state 置回 UNKNOWN），
    # 并恢复拓扑（把软删时释放的子项重新挂回 USING）。
    REMOVED = "removed"


# 处于这些状态的超级设备「不可用」：不能作为超级设备的子项（层叠），
# 也不能作为卷的挂载对象。判据是「能否承载数据」，与健康状况无关 ——
# DANGER / DEGRADING（降级但仍在运行）仍算可用。
UNAVAILABLE_SUPER_DEVICE_STATES = frozenset({SuperDeviceState.REMOVED, SuperDeviceState.FAULT})


# ═══════════════════════════════════════════
#  关联状态
# ═══════════════════════════════════════════

class SuperDeviceRelationState(enum.Enum):
    """超级设备-子项 关联状态枚举（`super_device_structures.state` 专用）。

    按「退役原因」区分，避免复活时误恢复：
    - REPLACED：因「换盘」退役，**不**随父行复活而恢复；
    - SUPER_DEVICE_REMOVED：因「父行软删」退役，可随 `revive_super_device` 恢复。

    注：super_volume_structures 用自己的一套（`domain/storage/super_volume/enum.py`
    的 SuperVolumeRelationState），两者不再共用枚举。
    """
    USING = "using"                                  # 正在使用
    REPLACED = "replaced"                            # 因换盘退役
    SUPER_DEVICE_REMOVED = "super_device_removed"    # 因父行软删退役（可随复活恢复）


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