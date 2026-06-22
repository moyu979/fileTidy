from __future__ import annotations

import enum
from dataclasses import dataclass


# ═══════════════════════════════════════════
#  超级设备状态
# ═══════════════════════════════════════════

class SuperDeviceState(enum.Enum):
    UNKNOWN = "unknown"   # 刚接入，尚未检测健康状态
    HEALTHY = "healthy"   # 正常使用
    DANGER = "danger"     # 危险，但暂时可用（有坏道等隐患）
    DEGRADING = "degrading"
    FAULT = "fault"       # 故障，无法使用
    REMOVED = "removed"   # 已移除（软删除，记录仍保留在数据库中）


@dataclass
class _SuperDeviceStateOption:
    """超级设备状态菜单选项内部结构"""
    code: str
    state: SuperDeviceState
    label: str
    desc: str


class SuperDeviceStateMenu:
    """超级设备状态菜单定义，可被 CLI / FastAPI 等前端复用。"""

    options: list[_SuperDeviceStateOption] = [
        _SuperDeviceStateOption("1", SuperDeviceState.UNKNOWN,   "UNKNOWN",  "未知（默认）"),
        _SuperDeviceStateOption("2", SuperDeviceState.HEALTHY,   "HEALTHY",  "健康"),
        _SuperDeviceStateOption("3", SuperDeviceState.DANGER,    "DANGER",   "危险"),
        _SuperDeviceStateOption("4", SuperDeviceState.DEGRADING, "DEGRADING","降级"),
        _SuperDeviceStateOption("5", SuperDeviceState.FAULT,     "FAULT",    "故障"),
        _SuperDeviceStateOption("6", SuperDeviceState.REMOVED,   "REMOVED",  "已移除"),
    ]

    _code_map: dict[str, SuperDeviceState] = {opt.code: opt.state for opt in options}
    _default: SuperDeviceState = SuperDeviceState.UNKNOWN

    @classmethod
    def prompt_text(cls) -> str:
        """生成菜单提示文本。"""
        lines = ["请选择超级设备状态:"]
        for opt in cls.options:
            lines.append(f"  {opt.code} — {opt.label} ({opt.desc})")
        return "\n".join(lines)

    @classmethod
    def input_hint(cls) -> str:
        """生成输入提示。"""
        codes = [opt.code for opt in cls.options]
        return f"请输入编号 ({'/'.join(codes)}，直接回车默认 {cls.options[0].code}): "

    @classmethod
    def from_code(cls, code: str) -> SuperDeviceState | None:
        """根据菜单编号返回 SuperDeviceState。

        返回 None 表示无法识别，调用方应循环询问。
        空字符串返回默认值 UNKNOWN。
        """
        key = code.strip()
        if not key:
            return cls._default
        return cls._code_map.get(key)


# ═══════════════════════════════════════════
#  关联状态
# ═══════════════════════════════════════════

class RelationState(enum.Enum):
    USING = "using"     # 正在使用
    UNUSED = "unused"   # 未使用，一般指代发生替换后之前的设备/卷


# ═══════════════════════════════════════════
#  超级设备类型
# ═══════════════════════════════════════════

@dataclass
class _SuperDeviceTypeOption:
    """超级设备类型菜单选项内部结构"""
    code: str
    type_str: str | None
    label: str
    desc: str


class SuperDeviceTypeMenu:
    """超级设备类型菜单定义，可被 CLI / FastAPI 等前端复用。"""

    options: list[_SuperDeviceTypeOption] = [
        _SuperDeviceTypeOption("1", "single", "单设备", "单个设备作为超级设备"),
        _SuperDeviceTypeOption("2", "raidz",  "RAID-Z", "RAID-Z 冗余阵列"),
    ]

    _code_map: dict[str, str] = {
        opt.code: opt.type_str
        for opt in options
        if opt.type_str is not None
    }

    @classmethod
    def prompt_text(cls) -> str:
        """生成菜单提示文本。"""
        lines = ["请选择超级设备类型（与系统编号一致）:"]
        for opt in cls.options:
            lines.append(f"  {opt.code} — {opt.label} ({opt.desc})")
        return "\n".join(lines)

    @classmethod
    def input_hint(cls) -> str:
        """生成输入提示。"""
        codes = [opt.code for opt in cls.options]
        return f"请输入编号 ({'/'.join(codes)}，直接回车默认 {cls.options[0].code}): "

    @classmethod
    def from_code(cls, code: str) -> str | None:
        """根据菜单编号返回超级设备 type 字符串。

        返回 None 表示无法识别，调用方应循环询问。
        空字符串返回 single（默认）。
        """
        key = code.strip()
        if not key:
            return cls.options[0].type_str
        return cls._code_map.get(key)