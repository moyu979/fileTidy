# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/get_path.py（门面转发）+ _util.as_device_path。

目的（测什么）：
    1. 门面 ``get_path`` 把序列号原样转给当前平台 ``get_path``，返回值透传；
    2. 私有模块 ``_util.py`` 的 ``as_device_path`` 归一化规则：看起来是路径
       （``/``、``~``、``./``、``../`` 开头或包含 ``/``）直接返回，否则当作
       序列号调平台 ``get_path``，解析不到时抛 ``ValueError``。
       （``_util.py`` 是私有模块，不单独建测试文件，断言并入本文件。）

输入：
    - 假平台模块（记录调用实参）；
    - 路径字符串、序列号字符串。

期望输出：
    - 平台返回的挂载点或 None；
    - 路径入参不经平台查询；未知序列号抛 ValueError。
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from infra.system.storage.device._util import as_device_path

_TARGET = "infra.system.storage.device.get_path"
_UTIL = "infra.system.storage.device._util"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _install_fake_platform(monkeypatch, module, fake):
    """把指定模块的 current_platform 替换为假平台模块。"""
    monkeypatch.setattr(module, "current_platform", lambda *a, **k: fake)


# ── 门面 get_path ────────────────────────────────────────────────────


def test_get_path_forwards_serial_and_returns_path(monkeypatch):
    """序列号入参 → 原样转给平台 get_path，挂载点透传。"""
    mod = _mod(_TARGET)
    seen: list[str] = []

    def fake_get_path(serial: str) -> str | None:
        seen.append(serial)
        return "/Volumes/Data"

    _install_fake_platform(monkeypatch, mod, SimpleNamespace(get_path=fake_get_path))

    assert mod.get_path("SN-001") == "/Volumes/Data"
    assert seen == ["SN-001"]


def test_get_path_returns_none_when_not_found(monkeypatch):
    """平台找不到对应设备路径 → 门面返回 None。"""
    mod = _mod(_TARGET)
    _install_fake_platform(
        monkeypatch, mod, SimpleNamespace(get_path=lambda serial: None),
    )

    assert mod.get_path("SN-404") is None


# ── _util.as_device_path ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "value",
    ["/dev/disk0", "/mnt/data", "~/Documents", "./relative", "../up/x", "dir/file"],
)
def test_as_device_path_passthrough_for_path_like_input(value, monkeypatch):
    """入参形态像路径 → 原样返回，且完全不查平台。"""
    util = _mod(_UTIL)

    def boom(*args, **kwargs):  # pragma: no cover - 不应被调用
        raise AssertionError("路径入参不应触发平台查询")

    _install_fake_platform(monkeypatch, util, SimpleNamespace(get_path=boom))

    assert as_device_path(value) == value


def test_as_device_path_resolves_serial_via_platform(monkeypatch):
    """入参不是路径 → 视为序列号，调当前平台 get_path 解析。"""
    util = _mod(_UTIL)
    seen: list[str] = []

    def fake_get_path(serial: str) -> str:
        seen.append(serial)
        return "/mnt/resolved"

    _install_fake_platform(monkeypatch, util, SimpleNamespace(get_path=fake_get_path))

    assert as_device_path("SN-123") == "/mnt/resolved"
    assert seen == ["SN-123"]


def test_as_device_path_unknown_serial_raises(monkeypatch):
    """平台 get_path 返回 None → 抛 ValueError，消息含原始入参。"""
    util = _mod(_UTIL)
    _install_fake_platform(
        monkeypatch, util, SimpleNamespace(get_path=lambda serial: None),
    )

    with pytest.raises(ValueError, match="SN-404"):
        as_device_path("SN-404")
