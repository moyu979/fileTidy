# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 SuperVolume 枚举定义 - 超级卷类型/状态常量

from __future__ import annotations

import enum

from domain.common.menu import _Menu, _MenuOption


# ═══════════════════════════════════════════
#  超级卷状态
# ═══════════════════════════════════════════

class SuperVolumeState(enum.Enum):
    """超级卷状态枚举。

    定义超级卷可能处于的各种健康状态。
    """
    UNKNOWN = "unknown"   # 刚创建，尚未检测健康状态
    HEALTHY = "healthy"   # 正常使用的
    DANGER = "danger"     # 危险，但暂时可用（有坏道等隐患）
    FAULT = "fault"       # 故障，无法使用
    REMOVED = "removed"   # 已移除（软删除，记录仍保留在数据库中）


class SuperVolumeStateMenu(_Menu):
    """超级卷状态菜单，可被 CLI / FastAPI 等前端复用。"""

    title = "超级卷状态"
    value_type = SuperVolumeState
    default = SuperVolumeState.UNKNOWN
    options = [
        _MenuOption("1", SuperVolumeState.UNKNOWN,  "UNKNOWN", "未知（默认）"),
        _MenuOption("2", SuperVolumeState.HEALTHY,  "HEALTHY", "健康"),
        _MenuOption("3", SuperVolumeState.DANGER,   "DANGER",  "危险"),
        _MenuOption("4", SuperVolumeState.FAULT,    "FAULT",   "故障"),
        _MenuOption("5", SuperVolumeState.REMOVED,  "REMOVED", "已移除"),
    ]


# ═══════════════════════════════════════════
#  超级卷类型
# ═══════════════════════════════════════════

class SuperVolumeTypeMenu(_Menu):
    """超级卷类型菜单，可被 CLI / FastAPI 等前端复用。"""

    title = "超级卷类型（与系统编号一致）"
    # value_type=None → from_code 直接返回类型字符串
    default = "copy"
    options = [
        _MenuOption("1", "copy",           "Copy",         "复制模式，多个卷内容保持一致"),
        _MenuOption("2", "snapraid_raid5", "SnapRAID RAID5", "SnapRAID RAID5 冗余阵列"),
    ]
