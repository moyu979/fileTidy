"""
容量换算工具。

支持带单位后缀的输入，采用千进制（K=10³, M=10⁶, G=10⁹, T=10¹²）。

使用场景：
  >>> parse_capacity("1T")
  1_000_000_000_000
  >>> format_capacity(1_500_000_000_000)
  '1.5T'
"""

from __future__ import annotations

# 千进制单位映射
_UNITS = {"K": 10**3, "M": 10**6, "G": 10**9, "T": 10**12}
_UNIT_NAMES = ["T", "G", "M", "K"]


def parse_capacity(text: str) -> int | None:
    """将用户输入的容量文本转为字节数（int）。

    支持格式：
      - 纯数字        → 直接作为字节数
      - 数字+单位后缀  → 千进制换算（不区分大小写）
      - 空串 / None   → 返回 None
    """
    if not text:
        return None
    raw = text.strip()
    if not raw:
        return None

    # 纯数字
    if raw.isdigit():
        return int(raw)

    # 数字 + 单位
    upper = raw.upper()
    suffix = upper[-1]
    prefix = upper[:-1]
    if suffix in _UNITS and prefix.isdigit():
        return int(prefix) * _UNITS[suffix]

    raise ValueError(f"无法解析容量: {text!r}")


def format_capacity(size_bytes: int) -> str:
    """将字节数格式化为带单位后缀的简短字符串（千进制，保留 2 位小数）。"""
    if size_bytes < 10**3:
        return str(size_bytes)
    for unit in _UNIT_NAMES:
        threshold = _UNITS[unit]
        if size_bytes >= threshold:
            value = size_bytes / threshold
            if value == int(value):
                return f"{int(value)}{unit}"
            return f"{value:.2f}{unit}"
    return str(size_bytes)
