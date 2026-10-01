# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/get_capacity.py（device 门面转发）。

目的（测什么）：
    验证门面 ``get_capacity`` 经 ``as_device_path`` 归一化后转发到当前平台
    ``get_capacity``：路径入参原样转发；序列号入参先解析为路径；解析失败抛
    ``ValueError``。容量以字节整数原样透传。

输入：
    - 假平台模块（记录调用实参）；
    - 路径 ``/dev/disk0``、序列号 ``SN-500``。

期望输出：
    - 平台返回的字节整数；
    - 未知序列号 → ValueError。
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

_TARGET = "infra.system.storage.device.get_capacity"
_UTIL = "infra.system.storage.device._util"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _install_fake_platform(monkeypatch, facade_mod, fake):
    """把门面与 _util 的 current_platform 一起替换为假平台模块。"""
    util = _mod(_UTIL)
    monkeypatch.setattr(facade_mod, "current_platform", lambda *a, **k: fake)
    monkeypatch.setattr(util, "current_platform", lambda *a, **k: fake)


def test_get_capacity_passthrough_for_path(monkeypatch):
    """输入是设备路径 → 平台 get_capacity 收到原路径，字节数透传。"""
    mod = _mod(_TARGET)
    seen: list[str] = []

    def fake_capacity(path: str) -> int:
        seen.append(path)
        return 500107862016

    _install_fake_platform(
        monkeypatch, mod, SimpleNamespace(get_capacity=fake_capacity),
    )

    assert mod.get_capacity("/dev/disk0") == 500107862016
    assert seen == ["/dev/disk0"]


def test_get_capacity_resolves_serial_first(monkeypatch):
    """输入是序列号 → 先解析为路径，再取该路径的容量。"""
    mod = _mod(_TARGET)
    resolved: list[str] = []
    seen: list[str] = []

    def fake_get_path(serial: str) -> str:
        resolved.append(serial)
        return "/mnt/data"

    def fake_capacity(path: str) -> int:
        seen.append(path)
        return 1234

    _install_fake_platform(
        monkeypatch, mod,
        SimpleNamespace(get_path=fake_get_path, get_capacity=fake_capacity),
    )

    assert mod.get_capacity("SN-500") == 1234
    assert resolved == ["SN-500"]
    assert seen == ["/mnt/data"]


def test_get_capacity_unknown_serial_raises(monkeypatch):
    """平台 get_path 返回 None → 抛 ValueError。"""
    mod = _mod(_TARGET)
    _install_fake_platform(
        monkeypatch, mod,
        SimpleNamespace(get_path=lambda serial: None, get_capacity=lambda path: 0),
    )

    with pytest.raises(ValueError, match="无法将"):
        mod.get_capacity("SN-404")
