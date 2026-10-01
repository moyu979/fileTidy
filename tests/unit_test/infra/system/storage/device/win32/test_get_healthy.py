# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/win32/get_healthy.py。

目的（测什么）：
    验证 win32 平台 get_healthy 解析 PowerShell 的 OperationalStatus/
    HealthStatus 输出：stdout 含 "OK" 或 "Healthy" → HEALTHY；否则 UNKNOWN。

输入：
    - 打桩 ``mod.subprocess`` 返回的假 PowerShell 输出，并记录命令行。

期望输出：
    - DeviceState.HEALTHY / UNKNOWN，且命令行使用 Get-PhysicalDisk。
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from domain.storage.device.enum import DeviceState

_TARGET = "infra.system.storage.device.win32.get_healthy"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _patch_subprocess(monkeypatch, mod, stdout: str, returncode: int = 0):
    """把模块内 subprocess 换成假实现，返回记录命令行的列表。"""
    calls: list[str] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=fake_run))
    return calls


@pytest.mark.parametrize(
    ("stdout", "expected"),
    [
        ("OperationalStatus : OK\nHealthStatus      : Healthy", DeviceState.HEALTHY),
        ("HealthStatus : Healthy", DeviceState.HEALTHY),
        ("OperationalStatus : OK", DeviceState.HEALTHY),
        ("OperationalStatus : Warning", DeviceState.UNKNOWN),
        ("", DeviceState.UNKNOWN),
    ],
)
def test_get_healthy_maps_powershell_output(monkeypatch, stdout, expected):
    """PowerShell stdout → 对应 DeviceState。"""
    mod = _mod(_TARGET)
    _patch_subprocess(monkeypatch, mod, stdout)

    assert mod.get_healthy("C:\\") is expected


def test_get_healthy_uses_get_physicaldisk_and_shell(monkeypatch):
    """调用 get_healthy("C:\\") → 经 shell 执行含 Get-PhysicalDisk 的单条命令。"""
    mod = _mod(_TARGET)
    calls = _patch_subprocess(monkeypatch, mod, "OK")

    mod.get_healthy("C:\\")

    assert len(calls) == 1
    assert "Get-PhysicalDisk" in calls[0]
