# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/get_type.py（device 门面转发）。

目的（测什么）：
    验证门面 ``get_type`` 走 ``as_device_path`` 归一化后再转发到当前平台
    ``get_type``：入参是路径时原样转发；入参是序列号时先用平台 ``get_path``
    解析成路径；序列号解析不出来时抛 ``ValueError``。

输入：
    - 假平台模块（记录被调用时收到的实参）；
    - 路径字符串 ``/dev/disk0``、序列号字符串 ``SN-001`` / ``SN-404``。

期望输出：
    - 型如 "ssd" / "hdd" 的类型字符串透传；
    - 平台 get_path 返回 None 时抛 ValueError。
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

_TARGET = "infra.system.storage.device.get_type"
_UTIL = "infra.system.storage.device._util"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _install_fake_platform(monkeypatch, facade_mod, fake):
    """把门面与 _util 的 current_platform 一起替换为假平台模块。"""
    util = _mod(_UTIL)
    monkeypatch.setattr(facade_mod, "current_platform", lambda *a, **k: fake)
    monkeypatch.setattr(util, "current_platform", lambda *a, **k: fake)


def test_get_type_passthrough_for_path(monkeypatch):
    """输入是设备路径 → 平台 get_type 收到原路径，类型字符串透传。"""
    mod = _mod(_TARGET)
    seen: list[str] = []

    def fake_type(path: str) -> str:
        seen.append(path)
        return "ssd"

    _install_fake_platform(monkeypatch, mod, SimpleNamespace(get_type=fake_type))

    assert mod.get_type("/dev/disk0") == "ssd"
    assert seen == ["/dev/disk0"]


def test_get_type_resolves_serial_first(monkeypatch):
    """输入是序列号 → 先调平台 get_path 解析为路径，再取类型。"""
    mod = _mod(_TARGET)
    resolved: list[str] = []
    seen: list[str] = []

    def fake_get_path(serial: str) -> str:
        resolved.append(serial)
        return "/dev/disk2"

    def fake_type(path: str) -> str:
        seen.append(path)
        return "hdd"

    _install_fake_platform(
        monkeypatch, mod,
        SimpleNamespace(get_path=fake_get_path, get_type=fake_type),
    )

    assert mod.get_type("SN-001") == "hdd"
    assert resolved == ["SN-001"]
    assert seen == ["/dev/disk2"]


def test_get_type_unknown_serial_raises(monkeypatch):
    """平台 get_path 返回 None → 无法归一化，抛 ValueError。"""
    mod = _mod(_TARGET)
    _install_fake_platform(
        monkeypatch, mod,
        SimpleNamespace(get_path=lambda serial: None, get_type=lambda path: "ssd"),
    )

    with pytest.raises(ValueError, match="无法将"):
        mod.get_type("SN-404")
