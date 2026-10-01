# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/darwin/get_healthy.py。

目的（测什么）：
    验证 darwin 平台 get_healthy 对 SMART Status 字段的映射（大小写不敏感）：
    "verified" → HEALTHY；"failing" → FAULT；"unsupported"/"not supported"
    以及任何其他值或缺失 → UNKNOWN。

输入：
    - 打桩 ``mod._disk_info`` 返回的 diskutil info 字典。

期望输出：
    - domain.storage.device.enum.DeviceState 的对应成员。
"""

from __future__ import annotations

import importlib

import pytest

from domain.storage.device.enum import DeviceState

_TARGET = "infra.system.storage.device.darwin.get_healthy"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("Verified", DeviceState.HEALTHY),
        ("verified", DeviceState.HEALTHY),
        ("Failing", DeviceState.FAULT),
        ("Not Supported", DeviceState.UNKNOWN),
        ("Unsupported", DeviceState.UNKNOWN),
        ("", DeviceState.UNKNOWN),
        ("something else", DeviceState.UNKNOWN),
    ],
)
def test_get_healthy_maps_smart_status(monkeypatch, status, expected):
    """SMART Status 文本 → 对应 DeviceState。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"SMART Status": status})

    assert mod.get_healthy("/dev/disk0") is expected


def test_get_healthy_missing_field_is_unknown(monkeypatch):
    """info 里没有 SMART Status 键 → UNKNOWN。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"Disk Size": "x"})

    assert mod.get_healthy("/dev/disk0") is DeviceState.UNKNOWN
