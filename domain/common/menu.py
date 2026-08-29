# CHECK: ai生成，待检查 - 领域共享菜单工具 - 通用菜单基类与选项

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _MenuOption:
    """菜单选项内部结构。"""
    code: str
    value: object
    label: str
    desc: str


class _Menu:
    """通用菜单基类：提供 prompt_text / input_hint / from_code。

    子类设置类属性：
      - title: 菜单标题（如 "设备状态"）
      - value_type: 可选；若提供，from_code 用 value_type(value) 转换（如枚举类）
      - default: 可选；空输入时返回的默认值（None 表示空输入返回 None）
      - options: _MenuOption 列表
    """
    title: str = ""
    value_type: type | None = None
    default: object = None
    options: list[_MenuOption] = []

    _code_map: dict[str, object] | None = None

    @classmethod
    def _ensure_maps(cls) -> None:
        """惰性构建 code → value 映射。"""
        if cls._code_map is None:
            cls._code_map = {opt.code: opt.value for opt in cls.options}

    @classmethod
    def prompt_text(cls) -> str:
        """生成菜单的提示文本。

        Returns:
            格式化后的菜单文本字符串，每行包含编号、标签和描述。
        """
        cls._ensure_maps()
        lines = [f"请选择{cls.title}:"]
        for opt in cls.options:
            lines.append(f"  {opt.code} — {opt.label} ({opt.desc})")
        return "\n".join(lines)

    @classmethod
    def input_hint(cls) -> str:
        """生成输入提示。

        Returns:
            提示字符串，列出可用的编号选项；有默认值时附带默认提示。
        """
        cls._ensure_maps()
        codes = [opt.code for opt in cls.options]
        hint = f"请输入编号 ({'/'.join(codes)}"
        if cls.default is not None:
            hint += f"，直接回车默认 {cls.options[0].code}"
        hint += "): "
        return hint

    @classmethod
    def from_code(cls, code: str):
        """根据菜单编号返回对应的值（枚举或字符串）。

        Args:
            code: 用户输入的菜单编号字符串。

        Returns:
            对应值；无法识别时返回 None，空字符串返回 default。
        """
        cls._ensure_maps()
        key = code.strip()
        if not key:
            return cls.default
        value = cls._code_map.get(key)
        if value is None:
            return None
        if cls.value_type is not None:
            return cls.value_type(value)
        return value
