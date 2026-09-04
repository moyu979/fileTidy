# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/runtime 与 device 平台分发门面。

目的：验证 set_os/current_os/resolve_platform/current_platform 的平台切换与
缓存失效，以及 as_device_path 的“路径直接返回 / 序列号查路径”归一化。

输入：set_os 平台名与假平台模块函数。
期望输出：正确的平台模块；无法解析的 serial 抛 ValueError。
"""

from __future__ import annotations

import pytest

import infra.system.runtime as runtime
from infra.system.storage.device._util import as_device_path


@pytest.fixture(autouse=True)
def _restore_runtime():
    original_os = runtime._os
    yield
    runtime._os = original_os
    runtime.reset()


def test_set_os_and_resolve_platform():
    """set_os('linux') → current_os/resolve_platform 均为 linux。"""
    runtime.set_os("linux")
    assert runtime.current_os() == "linux"
    assert runtime.resolve_platform() == "linux"


def test_unknown_os_falls_back_to_unknown_package():
    """未知 OS → 解析为 unknown 平台包。"""
    runtime.set_os("solaris")
    module = runtime.current_platform("device")
    assert module.__name__ == "infra.system.storage.device.unknown"


def test_platform_modules_differ_per_os():
    """不同 OS → 返回不同平台模块；reset 清缓存。"""
    runtime.set_os("darwin")
    darwin_mod = runtime.current_platform("device")
    runtime.set_os("linux")
    linux_mod = runtime.current_platform("device")
    assert darwin_mod is not linux_mod
    assert linux_mod.__name__ == "infra.system.storage.device.linux"


def test_as_device_path_passthrough_for_path():
    """输入看起来是路径 → 原样返回，不调用平台函数。"""
    assert as_device_path("/dev/disk0") == "/dev/disk0"


def test_as_device_path_resolves_serial(monkeypatch):
    """输入序列号 → 调平台 get_path 解析。"""
    runtime.set_os("darwin")
    fake = runtime.current_platform("device")
    monkeypatch.setattr(fake, "get_path", lambda serial: "/mnt/mac")
    assert as_device_path("SN-123") == "/mnt/mac"


def test_as_device_path_unknown_serial_raises(monkeypatch):
    """平台 get_path 返回 None → ValueError。"""
    runtime.set_os("darwin")
    fake = runtime.current_platform("device")
    monkeypatch.setattr(fake, "get_path", lambda serial: None)
    with pytest.raises(ValueError):
        as_device_path("SN-404")


def test_facade_forwards_to_current_platform(monkeypatch):
    """device 门面 get_serial → 转发到当前平台模块。"""
    import importlib

    facade = importlib.import_module("infra.system.storage.device.get_serial")
    from infra.system.runtime import current_platform

    runtime.set_os("darwin")
    fake = current_platform("device")
    monkeypatch.setattr(fake, "get_serial", lambda path: "RESOLVED")
    assert facade.get_serial("/dev/disk0") == "RESOLVED"
