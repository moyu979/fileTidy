from __future__ import annotations

import enum
from dataclasses import dataclass


class SuperVolumeState(enum.Enum):
    UNKNOWN = "unknown"   # 刚创建，尚未检测健康状态
    HEALTHY = "healthy"   # 正常使用的
    DANGER = "danger"     # 危险，但暂时可用（有坏道等隐患）
    FAULT = "fault"       # 故障，无法使用
    REMOVED = "removed"   # 已移除（软删除，记录仍保留在数据库中）


@dataclass
class _SuperVolumeStateOption:
    """超级卷状态菜单选项内部结构"""
    code: str
    state: SuperVolumeState
    label: str
    desc: str


class SuperVolumeStateMenu:
    """超级卷状态菜单定义，可被 CLI / FastAPI 等前端复用。"""

    options: list[_SuperVolumeStateOption] = [
        _SuperVolumeStateOption("1", SuperVolumeState.UNKNOWN,  "UNKNOWN", "未知（默认）"),
        _SuperVolumeStateOption("2", SuperVolumeState.HEALTHY,  "HEALTHY", "健康"),
        _SuperVolumeStateOption("3", SuperVolumeState.DANGER,   "DANGER",  "危险"),
        _SuperVolumeStateOption("4", SuperVolumeState.FAULT,    "FAULT",   "故障"),
        _SuperVolumeStateOption("5", SuperVolumeState.REMOVED,  "REMOVED", "已移除"),
    ]

    _code_map: dict[str, SuperVolumeState] = {opt.code: opt.state for opt in options}
    _default: SuperVolumeState = SuperVolumeState.UNKNOWN

    @classmethod
    def prompt_text(cls) -> str:
        """生成菜单提示文本。"""
        lines = ["请选择超级卷状态:"]
        for opt in cls.options:
            lines.append(f"  {opt.code} — {opt.label} ({opt.desc})")
        return "\n".join(lines)

    @classmethod
    def input_hint(cls) -> str:
        """生成输入提示。"""
        codes = [opt.code for opt in cls.options]
        return f"请输入编号 ({'/'.join(codes)}，直接回车默认 {cls.options[0].code}): "

    @classmethod
    def from_code(cls, code: str) -> SuperVolumeState:
        """根据编号字符串返回对应的 SuperVolumeState，无效编号返回默认值。"""
        return cls._code_map.get(code, cls._default)