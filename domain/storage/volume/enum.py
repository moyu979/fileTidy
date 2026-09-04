# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 Volume 枚举定义 - 卷类型/状态常量

from __future__ import annotations

import enum

from domain.common.menu import _Menu, _MenuOption


class VolumeState(enum.Enum):
    """卷状态枚举。

    定义卷（逻辑存储单元）可能处于的各种健康状态。
    """
    UNKNOWN = "unknown"   # 刚创建，尚未检测健康状态
    HEALTHY = "healthy"   # 正常使用的
    DANGER = "danger"     # 危险，但暂时可用（有坏道等隐患）
    FAULT = "fault"       # 故障，无法使用
    REMOVED = "removed"   # 已移除（软删除，记录仍保留在数据库中）


class VolumeStateMenu(_Menu):
    """卷状态菜单定义，可被 CLI / FastAPI 等前端复用。"""

    title = "卷状态"
    value_type = VolumeState
    default = VolumeState.UNKNOWN
    options = [
        _MenuOption("1", VolumeState.UNKNOWN,  "UNKNOWN", "未知（默认）"),
        _MenuOption("2", VolumeState.HEALTHY,  "HEALTHY", "健康"),
        _MenuOption("3", VolumeState.DANGER,   "DANGER",  "危险"),
        _MenuOption("4", VolumeState.FAULT,    "FAULT",   "故障"),
        _MenuOption("5", VolumeState.REMOVED,  "REMOVED", "已移除"),
    ]


# ═══════════════════════════════════════════
#  卷类型（文件系统类型）
# ═══════════════════════════════════════════

class VolumeTypeMenu(_Menu):
    """卷类型菜单定义，可被 CLI / FastAPI 等前端复用。"""

    title = "卷类型（文件系统类型）"
    options = [
        _MenuOption("1", "ntfs",   "NTFS",    "Windows NT 文件系统"),
        _MenuOption("2", "exfat",  "exFAT",   "扩展文件分配表"),
        _MenuOption("3", "fat32",  "FAT32",   "文件分配表 32"),
        _MenuOption("4", "ltfs",   "LTFS",    "线性磁带文件系统"),
    ]

    @classmethod
    def from_code(cls, code: str) -> str | None:
        """根据菜单编号或文件系统类型字符串返回卷类型。

        基类按编号匹配，这里额外支持直接输入类型字符串（如 "ntfs"）。

        Args:
            code: 用户输入的菜单编号或直接的文件系统类型字符串。

        Returns:
            对应的文件系统类型字符串；无法识别时返回 None。
        """
        result = super().from_code(code)
        if result is not None:
            return result
        key = code.strip()
        for opt in cls.options:
            if key == opt.value:
                return opt.value
        return None
