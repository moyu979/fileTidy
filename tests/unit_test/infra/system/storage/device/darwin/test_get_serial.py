# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/darwin/get_serial.py。

目的（测什么）：
    验证 darwin 平台 get_serial 只在 info 中存在 "Serial Number" 键时返回
    其值；键存在但值为空串时返回 None（分区设备无序列号）；键缺失返回 None。

输入：
    - 打桩 ``mod._disk_info`` 返回的 diskutil info 字典。

期望输出：
    - 序列号字符串或 None。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.darwin.get_serial"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def test_get_serial_returns_value(monkeypatch):
    """Serial Number 键存在且非空 → 返回该值。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"Serial Number": "AAA123"})

    assert mod.get_serial("/dev/disk0") == "AAA123"


@pytest.mark.parametrize(
    "info",
    [
        {"Serial Number": ""},
        {},
        {"Device / Media Name": "Apple SSD"},
    ],
)
def test_get_serial_returns_none(monkeypatch, info):
    """键缺失或值为空 → None。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: info)

    assert mod.get_serial("/dev/disk0s1") is None
