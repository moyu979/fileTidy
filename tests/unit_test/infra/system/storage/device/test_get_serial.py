# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/get_serial.py（device 门面转发）。

目的（测什么）：
    验证门面 ``get_serial`` 只接受路径、不做序列号归一化，直接把入参透传给
    当前平台的 ``get_serial``，并原样返回序列号或 None。

输入：
    - 假平台模块（记录调用实参）；
    - 设备路径 ``/dev/disk0``、``/mnt/vol1``。

期望输出：
    - 平台返回的序列号字符串；平台返回 None 时门面也返回 None。
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

_TARGET = "infra.system.storage.device.get_serial"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _install_fake_platform(monkeypatch, facade_mod, fake):
    """替换门面的 current_platform 为假平台模块。"""
    monkeypatch.setattr(facade_mod, "current_platform", lambda *a, **k: fake)


def test_get_serial_forwards_path_and_returns_value(monkeypatch):
    """路径入参 → 原样转给平台 get_serial，序列号透传。"""
    mod = _mod(_TARGET)
    seen: list[str] = []

    def fake_serial(path: str) -> str | None:
        seen.append(path)
        return "SERIAL-XYZ"

    _install_fake_platform(monkeypatch, mod, SimpleNamespace(get_serial=fake_serial))

    assert mod.get_serial("/dev/disk0") == "SERIAL-XYZ"
    assert seen == ["/dev/disk0"]


def test_get_serial_returns_none_when_platform_has_none(monkeypatch):
    """平台返回 None（如分区设备）→ 门面返回 None。"""
    mod = _mod(_TARGET)
    _install_fake_platform(
        monkeypatch, mod, SimpleNamespace(get_serial=lambda path: None),
    )

    assert mod.get_serial("/mnt/vol1") is None


def test_get_serial_does_not_treat_input_as_serial(monkeypatch):
    """入参不像路径（"weird-input"）→ 仍原样转发给平台 get_serial，不调用 get_path。"""
    mod = _mod(_TARGET)
    calls: list[str] = []

    def fake_get_path(serial: str):  # pragma: no cover - 不应被调用
        calls.append(serial)
        raise AssertionError("get_serial 门面不应调用平台 get_path")

    _install_fake_platform(
        monkeypatch, mod,
        SimpleNamespace(get_serial=lambda path: "S", get_path=fake_get_path),
    )

    assert mod.get_serial("weird-input") == "S"
    assert calls == []
