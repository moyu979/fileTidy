# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/linux/get_capacity.py（含 _common._parse_size）。

目的（测什么）：
    1. get_capacity 取 lsblk 的 "size" 字段并交给 ``_parse_size`` 换算字节；
    2. 私有 ``_common._parse_size`` 的换算规则：K/M/G/T 后缀按 1024 进制，
       小数用 float 解析后取整，无后缀则按裸字节解析（不单独建测试文件，
       断言并入本文件）。

输入：
    - 打桩 ``mod._disk_info`` 返回的 lsblk 设备字典；
    - 直接调用 ``_parse_size`` 的容量字符串。

期望输出：
    - 字节整数；（记录）无后缀非法字符串会抛 ValueError。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.linux.get_capacity"
_COMMON = "infra.system.storage.device.linux._common"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        ("100G", 100 * 1024**3),
        ("1T", 1024**4),
        ("500M", 500 * 1024**2),
        ("4K", 4 * 1024),
        ("238.5G", int(238.5 * 1024**3)),
    ],
)
def test_get_capacity_parses_size_field(monkeypatch, size, expected):
    """lsblk size 文本 → 字节整数（1024 进制）。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"name": "sda", "size": size})

    assert mod.get_capacity("/dev/sda") == expected


def test_get_capacity_defaults_to_zero_suffix_less(monkeypatch):
    """size 字段缺失 → 默认 "0" → 0 字节。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"name": "sda"})

    assert mod.get_capacity("/dev/sda") == 0


# ── 私有 _common._parse_size（间接覆盖） ─────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (" 100g ", 100 * 1024**3),
        ("1t", 1024**4),
        ("2048", 2048),
    ],
)
def test_parse_size_is_case_and_space_insensitive(raw, expected):
    """大小写混写、含首尾空白的容量串 → 解析结果与规范写法一致。"""
    common = _mod(_COMMON)

    assert common._parse_size(raw) == expected


def test_parse_size_with_unknown_suffix_raises():
    """无法识别的后缀（如 lsblk 的 "0B"）→ 抛 ValueError（记录既有行为）。"""
    common = _mod(_COMMON)

    with pytest.raises(ValueError):
        common._parse_size("0B")
