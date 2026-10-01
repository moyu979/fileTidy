# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/linux/get_serial.py。

目的（测什么）：
    验证 linux 平台 get_serial 返回 lsblk "serial" 字段：有值返回字符串；
    字段缺失、为 None 或为空串时返回 None。

输入：
    - 打桩 ``mod._disk_info`` 返回的 lsblk 设备字典。

期望输出：
    - 序列号字符串或 None。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.linux.get_serial"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def test_get_serial_returns_value(monkeypatch):
    """serial 字段有值 → 原样返回。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"serial": "LINUX-SN"})

    assert mod.get_serial("/dev/sda") == "LINUX-SN"


@pytest.mark.parametrize(
    "info",
    [
        {},
        {"serial": None},
        {"serial": ""},
    ],
)
def test_get_serial_returns_none(monkeypatch, info):
    """serial 缺失/None/空串 → None。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: info)

    assert mod.get_serial("/dev/sda") is None
