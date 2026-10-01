# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/linux/is_disk.py。

目的（测什么）：
    验证 linux 平台 is_disk 以「能否成功执行 _disk_info」为判据：
    成功 → True；抛 RuntimeError → False；其他异常不被吞掉。

输入：
    - 打桩 ``mod._disk_info`` 正常返回 / 抛 RuntimeError / 抛 KeyError。

期望输出：
    - True / False；KeyError 向上传播。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.linux.is_disk"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def test_is_disk_true_when_info_succeeds(monkeypatch):
    """_disk_info 成功 → True。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"name": "sda"})

    assert mod.is_disk("/dev/sda") is True


def test_is_disk_false_on_runtime_error(monkeypatch):
    """_disk_info 抛 RuntimeError → False。"""
    mod = _mod(_TARGET)

    def boom(path):
        raise RuntimeError("无法通过 lsblk 找到设备")

    monkeypatch.setattr(mod, "_disk_info", boom)

    assert mod.is_disk("/not/a/disk") is False


def test_is_disk_propagates_unexpected_error(monkeypatch):
    """_disk_info 抛 KeyError（非 RuntimeError）→ KeyError 向上传播。"""
    mod = _mod(_TARGET)

    def boom(path):
        raise KeyError("unexpected")

    monkeypatch.setattr(mod, "_disk_info", boom)

    with pytest.raises(KeyError):
        mod.is_disk("/dev/sda")
