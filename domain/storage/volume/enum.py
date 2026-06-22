from __future__ import annotations

import enum
from dataclasses import dataclass


class VolumeState(enum.Enum):
    UNKNOWN = "unknown"   # 刚创建，尚未检测健康状态
    HEALTHY = "healthy"   # 正常使用的
    DANGER = "danger"     # 危险，但暂时可用（有坏道等隐患）
    FAULT = "fault"       # 故障，无法使用
    REMOVED = "removed"   # 已移除（软删除，记录仍保留在数据库中）


@dataclass
class _VolumeStateOption:
    """卷状态菜单选项内部结构"""
    code: str
    state: VolumeState
    label: str
    desc: str


class VolumeStateMenu:
    """卷状态菜单定义，可被 CLI / FastAPI 等前端复用。"""

    options: list[_VolumeStateOption] = [
        _VolumeStateOption("1", VolumeState.UNKNOWN,  "UNKNOWN", "未知（默认）"),
        _VolumeStateOption("2", VolumeState.HEALTHY,  "HEALTHY", "健康"),
        _VolumeStateOption("3", VolumeState.DANGER,   "DANGER",  "危险"),
        _VolumeStateOption("4", VolumeState.FAULT,    "FAULT",   "故障"),
        _VolumeStateOption("5", VolumeState.REMOVED,  "REMOVED", "已移除"),
    ]

    _code_map: dict[str, VolumeState] = {opt.code: opt.state for opt in options}
    _default: VolumeState = VolumeState.UNKNOWN

    @classmethod
    def prompt_text(cls) -> str:
        """生成菜单提示文本。"""
        lines = ["请选择卷状态:"]
        for opt in cls.options:
            lines.append(f"  {opt.code} — {opt.label} ({opt.desc})")
        return "\n".join(lines)

    @classmethod
    def input_hint(cls) -> str:
        """生成输入提示。"""
        codes = [opt.code for opt in cls.options]
        return f"请输入编号 ({'/'.join(codes)}，直接回车默认 {cls.options[0].code}): "

    @classmethod
    def from_code(cls, code: str) -> VolumeState:
        """根据编号字符串返回对应的 VolumeState，无效编号返回默认值。"""
        return cls._code_map.get(code, cls._default)


# ═══════════════════════════════════════════
#  卷类型（文件系统类型）
# ═══════════════════════════════════════════

@dataclass
class _VolumeTypeOption:
    """卷类型菜单选项内部结构"""
    code: str
    type_str: str | None
    label: str
    desc: str


class VolumeTypeMenu:
    """卷类型菜单定义，可被 CLI / FastAPI 等前端复用。"""

    options: list[_VolumeTypeOption] = [
        _VolumeTypeOption("1", "ntfs",   "NTFS",    "Windows NT 文件系统"),
        _VolumeTypeOption("2", "exfat",  "exFAT",   "扩展文件分配表"),
        _VolumeTypeOption("3", "fat32",  "FAT32",   "文件分配表 32"),
        _VolumeTypeOption("4", "ltfs",   "LTFS",    "线性磁带文件系统"),
    ]

    _code_map: dict[str, str] = {
        opt.code: opt.type_str
        for opt in options
        if opt.type_str is not None
    }

    @classmethod
    def prompt_text(cls) -> str:
        """生成菜单提示文本。"""
        lines = ["请选择卷类型（文件系统类型）:"]
        for opt in cls.options:
            lines.append(f"  {opt.code} — {opt.label} ({opt.desc})")
        return "\n".join(lines)

    @classmethod
    def input_hint(cls) -> str:
        """生成输入提示。"""
        codes = [opt.code for opt in cls.options]
        return f"请输入编号 ({'/'.join(codes)}): "

    @classmethod
    def from_code(cls, code: str) -> str | None:
        """根据菜单编号返回卷 type 字符串。

        返回 None → 无法识别，调用方应循环询问。
        其他字符串 → 对应的文件系统类型值。
        """
        key = code.strip()
        if not key:
            return None
        if key in cls._code_map:
            return cls._code_map[key]
        # 支持直接输入字符串（如 "ntfs"），跳过菜单编号逻辑
        for type_str in cls._code_map.values():
            if type_str == key:
                return type_str
        return None