# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/is_disk.py（device 门面转发）。

目的（测什么）：
    验证门面 ``is_disk`` 经 ``as_device_path`` 归一化后转发到当前平台
    ``is_disk``：布尔结果透传；序列号先解析为路径；序列号无法解析时抛
    ``ValueError``。

输入：
    - 假平台模块（记录调用实参）；
    - 路径 ``/dev/disk0``、序列号 ``SN-777``。

期望输出：
    - True / False；未知序列号 → ValueError。
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

_TARGET = "infra.system.storage.device.is_disk"
_UTIL = "infra.system.storage.device._util"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _install_fake_platform(monkeypatch, facade_mod, fake):
    """把门面与 _util 的 current_platform 一起替换为假平台模块。"""
    util = _mod(_UTIL)
    monkeypatch.setattr(facade_mod, "current_platform", lambda *a, **k: fake)
    monkeypatch.setattr(util, "current_platform", lambda *a, **k: fake)


@pytest.mark.parametrize("platform_result", [True, False])
def test_is_disk_passthrough_for_path(monkeypatch, platform_result):
    """输入是设备路径 → 平台 is_disk 收到原路径，布尔值透传。"""
    mod = _mod(_TARGET)
    seen: list[str] = []

    def fake_is_disk(path: str) -> bool:
        seen.append(path)
        return platform_result

    _install_fake_platform(
        monkeypatch, mod, SimpleNamespace(is_disk=fake_is_disk),
    )

    assert mod.is_disk("/dev/disk0") is platform_result
    assert seen == ["/dev/disk0"]


def test_is_disk_resolves_serial_first(monkeypatch):
    """输入是序列号 → 先解析为路径，再判断该路径是否为磁盘。"""
    mod = _mod(_TARGET)
    seen: list[str] = []

    def fake_is_disk(path: str) -> bool:
        seen.append(path)
        return True

    _install_fake_platform(
        monkeypatch, mod,
        SimpleNamespace(get_path=lambda serial: "/dev/disk5", is_disk=fake_is_disk),
    )

    assert mod.is_disk("SN-777") is True
    assert seen == ["/dev/disk5"]


def test_is_disk_unknown_serial_raises(monkeypatch):
    """平台 get_path 返回 None → 抛 ValueError。"""
    mod = _mod(_TARGET)
    _install_fake_platform(
        monkeypatch, mod,
        SimpleNamespace(get_path=lambda serial: None, is_disk=lambda path: False),
    )

    with pytest.raises(ValueError, match="无法将"):
        mod.is_disk("SN-404")
