# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/get_healthy.py（device 门面转发）。

目的（测什么）：
    验证门面 ``get_healthy`` 经 ``as_device_path`` 归一化后转发到当前平台
    ``get_healthy``，并把平台返回的 ``DeviceState`` 枚举原样透传；序列号无法
    解析为路径时抛 ``ValueError``。

输入：
    - 假平台模块（记录调用实参）；
    - 路径 ``/dev/disk0``、序列号 ``SN-900``。

期望输出：
    - DeviceState 枚举成员（用 ``is`` 判定同一性）；
    - 未知序列号 → ValueError。
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from domain.storage.device.enum import DeviceState

_TARGET = "infra.system.storage.device.get_healthy"
_UTIL = "infra.system.storage.device._util"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _install_fake_platform(monkeypatch, facade_mod, fake):
    """把门面与 _util 的 current_platform 一起替换为假平台模块。"""
    util = _mod(_UTIL)
    monkeypatch.setattr(facade_mod, "current_platform", lambda *a, **k: fake)
    monkeypatch.setattr(util, "current_platform", lambda *a, **k: fake)


def test_get_healthy_passthrough_for_path(monkeypatch):
    """输入是设备路径 → 平台 get_healthy 收到原路径，枚举透传。"""
    mod = _mod(_TARGET)
    seen: list[str] = []

    def fake_healthy(path: str) -> DeviceState:
        seen.append(path)
        return DeviceState.HEALTHY

    _install_fake_platform(
        monkeypatch, mod, SimpleNamespace(get_healthy=fake_healthy),
    )

    assert mod.get_healthy("/dev/disk0") is DeviceState.HEALTHY
    assert seen == ["/dev/disk0"]


def test_get_healthy_resolves_serial_first(monkeypatch):
    """输入是序列号 → 先解析为路径，再取该路径的健康状态。"""
    mod = _mod(_TARGET)
    seen: list[str] = []

    def fake_healthy(path: str) -> DeviceState:
        seen.append(path)
        return DeviceState.FAULT

    _install_fake_platform(
        monkeypatch, mod,
        SimpleNamespace(get_path=lambda serial: "/dev/disk9", get_healthy=fake_healthy),
    )

    assert mod.get_healthy("SN-900") is DeviceState.FAULT
    assert seen == ["/dev/disk9"]


def test_get_healthy_unknown_serial_raises(monkeypatch):
    """平台 get_path 返回 None → 抛 ValueError。"""
    mod = _mod(_TARGET)
    _install_fake_platform(
        monkeypatch, mod,
        SimpleNamespace(
            get_path=lambda serial: None,
            get_healthy=lambda path: DeviceState.UNKNOWN,
        ),
    )

    with pytest.raises(ValueError, match="无法将"):
        mod.get_healthy("SN-404")
