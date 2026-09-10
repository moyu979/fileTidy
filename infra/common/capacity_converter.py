"""
容量换算工具。

支持带单位后缀的输入，可指定进制：
- ``base=1000``（默认，千进制）— 适配硬盘容量（K=10³, M=10⁶, G=10⁹, T=10¹²）
- ``base=1024``（二进制）— 适配内存等（K=2¹⁰, M=2²⁰, G=2³⁰, T=2⁴⁰）

使用场景：
  >>> parse_capacity("1T")                    # 默认 1000 进制
  1000000000000
  >>> parse_capacity("1T", base=1024)         # 1024 进制
  1099511627776
  >>> parse_capacity("1.5T")                  # 支持小数前缀
  1500000000000
  >>> format_capacity(1_500_000_000_000)      # 默认 1000 进制
  '1.50T'
  >>> format_capacity(17_179_869_184, base=1024)
  '16G'
"""

from __future__ import annotations

# 支持的进制
_BASES = (1000, 1024)

# 单位后缀（从大到小排列，格式化时优先匹配大单位）
_UNIT_NAMES = ("T", "G", "M", "K")


def _validate_base(base: int) -> None:
    """校验进制参数是否合法。

    Raises:
        ValueError: base 不在 {1000, 1024} 中时抛出。
    """
    if base not in _BASES:
        raise ValueError(f"不支持的进制: {base!r}，仅支持 {_BASES}")


def parse_capacity(text: str, base: int = 1000) -> int | None:
    """将用户输入的容量文本转为字节数（int）。

    支持格式：
      - 纯数字              → 直接作为字节数
      - 数字+单位后缀        → 按指定进制换算（不区分大小写）
      - 小数+单位后缀        → 按指定进制换算，如 "1.5T"
      - 空串 / None         → 返回 None

    Args:
        text: 容量文本，如 "1T", "1.5T", "1024", "500G"。
        base: 进制，1000（千进制，适配硬盘）或 1024（二进制，适配内存）。

    Returns:
        转换后的字节整数值，输入为空时返回 None。

    Raises:
        ValueError: 无法解析的格式或非法进制时抛出。
    """
    if not text:
        return None
    raw = text.strip()
    if not raw:
        return None

    # 纯数字
    if raw.isdigit():
        return int(raw)

    # 数字/小数 + 单位
    upper = raw.upper()
    suffix = upper[-1]
    prefix = upper[:-1]
    if suffix in _UNIT_NAMES:
        _validate_base(base)
        # 单位在 _UNIT_NAMES 中的位置决定幂次：K=1, M=2, G=3, T=4
        power = len(_UNIT_NAMES) - _UNIT_NAMES.index(suffix)
        try:
            number = float(prefix)
        except ValueError as exc:
            raise ValueError(f"无法解析容量: {text!r}") from exc
        return int(number * base**power)

    raise ValueError(f"无法解析容量: {text!r}")


def format_capacity(size_bytes: int, base: int = 1000) -> str:
    """将字节数格式化为带单位后缀的简短字符串（保留 2 位小数）。

    Args:
        size_bytes: 字节整数值。
        base: 进制，1000（千进制，适配硬盘）或 1024（二进制，适配内存）。

    Returns:
        格式化后的容量字符串，如 "1.5T", "500G"。
    """
    _validate_base(base)
    if size_bytes < base:
        return str(size_bytes)
    for i, unit in enumerate(_UNIT_NAMES):
        # i=0 对应 T（base^4），i=3 对应 K（base^1）
        threshold = base ** (len(_UNIT_NAMES) - i)
        if size_bytes >= threshold:
            value = size_bytes / threshold
            if value == int(value):
                return f"{int(value)}{unit}"
            return f"{value:.2f}{unit}"
    return str(size_bytes)
