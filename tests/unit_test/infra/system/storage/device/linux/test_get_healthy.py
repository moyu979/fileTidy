# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/linux/get_healthy.py。

目的（测什么）：
    验证 linux 平台 get_healthy 先用 _disk_info 取出原始盘名拼 ``/dev/<name>``，
    再调 ``smartctl -H``：命令非零退出 → UNKNOWN；stdout 含 "PASSED" →
    HEALTHY；含 "FAILED" → FAULT；两者都不含 → UNKNOWN。

输入：
    - 打桩 ``mod._disk_info`` 返回 ``{"name": "sda"}``；
    - 打桩 ``mod.subprocess`` 返回假 smartctl 结果，并记录被调用的命令行。

期望输出：
    - DeviceState.HEALTHY / FAULT / UNKNOWN，且命令行含 ``/dev/sda``。
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from domain.storage.device.enum import DeviceState

_TARGET = "infra.system.storage.device.linux.get_healthy"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _patch_subprocess(monkeypatch, mod, stdout: str, returncode: int = 0):
    """把模块内 subprocess 换成假实现，返回记录命令行的列表。"""
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=fake_run))
    return calls


@pytest.mark.parametrize(
    ("stdout", "returncode", "expected"),
    [
        ("SMART overall-health self-assessment test result: PASSED", 0, DeviceState.HEALTHY),
        ("SMART overall-health self-assessment test result: FAILED!", 0, DeviceState.FAULT),
        ("SMART support is: Unavailable", 0, DeviceState.UNKNOWN),
        ("", 1, DeviceState.UNKNOWN),
    ],
)
def test_get_healthy_maps_smartctl_output(monkeypatch, stdout, returncode, expected):
    """smartctl stdout/退出码 → 对应 DeviceState。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"name": "sda"})
    _patch_subprocess(monkeypatch, mod, stdout, returncode)

    assert mod.get_healthy("/dev/sda") is expected


def test_get_healthy_queries_raw_device_name(monkeypatch):
    """_disk_info 给出 name=nvme0n1 → 命令行使用 /dev/nvme0n1，返回 HEALTHY。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"name": "nvme0n1"})
    calls = _patch_subprocess(monkeypatch, mod, "PASSED")

    assert mod.get_healthy("/mnt/data") is DeviceState.HEALTHY
    assert calls == [["smartctl", "-H", "/dev/nvme0n1"]]


def test_get_healthy_propagates_disk_info_runtime_error(monkeypatch):
    """_disk_info 找不到设备抛 RuntimeError → 异常向上传播。"""
    mod = _mod(_TARGET)

    def boom(path):
        raise RuntimeError("无法通过 lsblk 找到设备")

    monkeypatch.setattr(mod, "_disk_info", boom)

    with pytest.raises(RuntimeError):
        mod.get_healthy("/nope")
