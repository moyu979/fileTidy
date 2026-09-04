# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/common/capacity_converter —— 容量换算。

目的：验证 parse_capacity（文本→字节）与 format_capacity（字节→文本）
在 1000/1024 双进制下的结果，以及非法输入/进制的异常。

输入：如 "1T"、"1.5T"、"1024"、空串；字节数。
期望输出：按文档换算出的整数或格式化字符串；非法输入抛 ValueError。
"""

from __future__ import annotations

import pytest

from infra.common.capacity_converter import format_capacity, parse_capacity


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1T", 1_000_000_000_000),
        ("1.5T", 1_500_000_000_000),
        ("500G", 500_000_000_000),
        ("2M", 2_000_000),
        ("3K", 3_000),
        ("1024", 1024),
        ("", None),
        (None, None),
    ],
)
def test_parse_capacity_decimal(text, expected):
    """千进制文本 → 字节数；空输入 → None。"""
    assert parse_capacity(text) == expected


def test_parse_capacity_binary():
    """base=1024 时 1T → 2^40。"""
    assert parse_capacity("1T", base=1024) == 1099511627776
    assert parse_capacity("16G", base=1024) == 17179869184


def test_parse_capacity_ignores_case():
    """小写后缀同样解析。"""
    assert parse_capacity("1t") == 1_000_000_000_000
    assert parse_capacity("1.5t") == 1_500_000_000_000


@pytest.mark.parametrize("text", ["abc", "1.5", "1TB", "12X", "1..2G"])
def test_parse_capacity_invalid(text):
    """无法解析的文本 → ValueError。"""
    with pytest.raises(ValueError):
        parse_capacity(text)


def test_invalid_base_rejected():
    """进制不在 {1000, 1024} → ValueError。"""
    with pytest.raises(ValueError):
        parse_capacity("1T", base=2)
    with pytest.raises(ValueError):
        format_capacity(1000, base=2)


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0"),
        (999, "999"),
        (1000, "1K"),
        (500_000_000_000, "500G"),
        (1_000_000_000_000, "1T"),
        (1_500_000_000_000, "1.50T"),
    ],
)
def test_format_capacity_decimal(size, expected):
    """千进制字节数 → 简短单位文本（整值不带小数）。"""
    assert format_capacity(size) == expected


def test_format_capacity_binary():
    """二进制字节数 → 2 进制单位文本。"""
    assert format_capacity(17179869184, base=1024) == "16G"
    assert format_capacity(1099511627776, base=1024) == "1T"
