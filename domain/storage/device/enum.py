from __future__ import annotations

import enum
from dataclasses import dataclass


class DeviceState(enum.Enum):
    UNKNOWN = "unknown" # 刚接入，尚未检测健康状态
    HEALTHY = "healthy" # 正常使用的
    DANGER = "danger" # 危险，但是暂时可以使用，主要用来描述有坏道等隐患的设备
    FAULT = "fault" # 故障，无法使用
    REMOVED = "removed" # 已移除（软删除，记录仍保留在数据库中）


@dataclass
class _DeviceStateOption:
    """菜单选项内部结构"""
    code: str
    state: DeviceState
    label: str
    desc: str


class DeviceStateMenu:
    """设备状态菜单定义，可被 CLI / FastAPI 等前端复用。"""

    options: list[_DeviceStateOption] = [
        _DeviceStateOption("1", DeviceState.UNKNOWN,  "UNKNOWN", "未知（默认）"),
        _DeviceStateOption("2", DeviceState.HEALTHY,  "HEALTHY", "健康"),
        _DeviceStateOption("3", DeviceState.DANGER,   "DANGER",  "危险"),
        _DeviceStateOption("4", DeviceState.FAULT,    "FAULT",   "故障"),
        _DeviceStateOption("5", DeviceState.REMOVED,  "REMOVED", "已移除"),
    ]

    _code_map: dict[str, DeviceState] = {opt.code: opt.state for opt in options}
    _default: DeviceState = DeviceState.UNKNOWN

    @classmethod
    def prompt_text(cls) -> str:
        """生成菜单提示文本。"""
        lines = ["请选择设备状态:"]
        for opt in cls.options:
            lines.append(f"  {opt.code} — {opt.label} ({opt.desc})")
        return "\n".join(lines)

    @classmethod
    def input_hint(cls) -> str:
        """生成输入提示。"""
        codes = [opt.code for opt in cls.options]
        return f"请输入编号 ({'/'.join(codes)}，直接回车默认 {cls.options[0].code}): "

    @classmethod
    def from_code(cls, code: str) -> DeviceState | None:
        """根据菜单编号返回 DeviceState。

        返回 None 表示无法识别，调用方应循环询问。
        空字符串返回默认值 UNKNOWN。
        """
        key = code.strip()
        if not key:
            return cls._default
        return cls._code_map.get(key)


@dataclass
class _DeviceTypeOption:
    """设备类型菜单选项内部结构"""
    code: str
    type_str: str | None
    label: str
    desc: str


class DeviceTypeMenu:
    """设备类型菜单定义，可被 CLI / FastAPI 等前端复用。

    特殊说明：
      - 磁带 (code="4") 需要额外输入 LTO 代次，如 "45" → Tape-lto5
      - type_str=None 的选项由 from_code 做特殊解析
    """

    options: list[_DeviceTypeOption] = [
        _DeviceTypeOption("1", "ssd",        "SSD",    "固态硬盘"),
        _DeviceTypeOption("2", "hdd",        "HDD",    "机械硬盘"),
        _DeviceTypeOption("3", "tf_sd_card", "TF 卡",  "tf_sd_card"),
        _DeviceTypeOption("4", None,         "磁带",   "需额外输入代次，如 45 表示 LTO5"),
    ]

    _code_map: dict[str, str] = {
        opt.code: opt.type_str
        for opt in options
        if opt.type_str is not None
    }

    @classmethod
    def prompt_text(cls) -> str:
        """生成菜单提示文本。"""
        lines = ["请选择设备类型:"]
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
        """根据菜单编号返回设备 type 字符串。

        返回 None  → 无法识别，调用方应循环询问。
        其他字符串 → 对应的 type 值。
        """
        key = code.strip()
        if not key:
            return None
        if key in cls._code_map:
            return cls._code_map[key]
        # 磁带特殊处理：第一个字符 "4" 是菜单编号，后续为 LTO 代次
        if key.startswith("4") and len(key) > 1:
            return f"Tape-lto{key[1:]}".lower()
        return None