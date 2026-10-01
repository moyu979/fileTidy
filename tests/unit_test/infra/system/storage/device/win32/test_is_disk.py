# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/win32/is_disk.py。

目的（测什么）：
    验证 win32 平台 is_disk 以「能否成功执行 _get_drive_by_path」为判据：
    成功 → True；抛 RuntimeError 或 subprocess.TimeoutExpired → False；
    其他异常不被吞掉。

输入：
    - 打桩 ``mod._get_drive_by_path`` 正常返回 / 抛异常。

期望输出：
    - True / False；KeyError 向上传播。
"""

from __future__ import annotations

import importlib
import subprocess

import pytest

_TARGET = "infra.system.storage.device.win32.is_disk"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def test_is_disk_true_when_drive_found(monkeypatch):
    """_get_drive_by_path 返回磁盘字典 → True。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_get_drive_by_path", lambda path: {"Index": "0"})

    assert mod.is_disk("C:\\") is True


def test_is_disk_false_on_runtime_error(monkeypatch):
    """_get_drive_by_path 抛 RuntimeError → False。"""
    mod = _mod(_TARGET)

    def boom(path):
        raise RuntimeError("无法找到路径对应的卷")

    monkeypatch.setattr(mod, "_get_drive_by_path", boom)

    assert mod.is_disk("Z:\\") is False


def test_is_disk_false_on_timeout(monkeypatch):
    """_get_drive_by_path 抛 subprocess.TimeoutExpired → False。"""
    mod = _mod(_TARGET)

    def timeout(path):
        raise subprocess.TimeoutExpired(cmd="powershell", timeout=5)

    monkeypatch.setattr(mod, "_get_drive_by_path", timeout)

    assert mod.is_disk("C:\\") is False


def test_is_disk_propagates_unexpected_error(monkeypatch):
    """_get_drive_by_path 抛 KeyError（不属于可捕获类型）→ KeyError 向上传播。"""
    mod = _mod(_TARGET)

    def boom(path):
        raise KeyError("unexpected")

    monkeypatch.setattr(mod, "_get_drive_by_path", boom)

    with pytest.raises(KeyError):
        mod.is_disk("C:\\")
