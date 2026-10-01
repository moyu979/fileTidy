# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/darwin/get_capacity.py。

目的（测什么）：
    验证 darwin 平台 get_capacity 从 diskutil info 的 "Disk Size" 字段中
    正则提取括号内字节数：``"(500107862016 Bytes)"`` → int；字段缺失或格式
    不含 ``(N Bytes)`` 时抛 ``ValueError``。

输入：
    - 打桩 ``mod._disk_info`` 返回的 diskutil info 字典。

期望输出：
    - 字节整数；无法解析时 ValueError。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.darwin.get_capacity"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("500.1 GB (500107862016 Bytes)", 500107862016),
        ("1.0 TB (1000204886016 Bytes)", 1000204886016),
        ("(1024 Bytes)", 1024),
    ],
)
def test_get_capacity_parses_bytes(monkeypatch, raw, expected):
    """Disk Size 文本 → 括号内字节整数。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"Disk Size": raw})

    assert mod.get_capacity("/dev/disk0") == expected


@pytest.mark.parametrize(
    "info",
    [
        {},
        {"Disk Size": "500.1 GB"},
        {"Disk Size": "unknown"},
    ],
)
def test_get_capacity_unparsable_raises(monkeypatch, info):
    """缺少 Disk Size 或格式不含字节数 → ValueError（消息含路径）。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: info)

    with pytest.raises(ValueError, match="无法解析容量"):
        mod.get_capacity("/dev/disk9")
