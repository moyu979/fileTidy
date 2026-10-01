# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/win32/get_capacity.py。

目的（测什么）：
    验证 win32 平台 get_capacity 从 diskdrive 字典的 "Size" 取值并转为 int；
    找不到磁盘或字典缺少 Size 键时抛 ValueError。

输入：
    - 打桩 ``mod._get_drive_by_path`` 返回的 diskdrive 字典。

期望输出：
    - 字节整数；缺失时 ValueError。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.win32.get_capacity"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


@pytest.mark.parametrize(
    ("drive", "expected"),
    [
        ({"Size": "500107862016"}, 500107862016),
        ({"Size": 1024}, 1024),
    ],
)
def test_get_capacity_returns_int(monkeypatch, drive, expected):
    """Size（字符串或整数）→ 字节整数。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_get_drive_by_path", lambda path: drive)

    assert mod.get_capacity("C:\\") == expected


@pytest.mark.parametrize(
    "drive",
    [None, {"SerialNumber": "SN-1"}],
)
def test_get_capacity_raises_when_missing(monkeypatch, drive):
    """磁盘找不到或没有 Size 字段 → ValueError。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_get_drive_by_path", lambda path: drive)

    with pytest.raises(ValueError, match="无法获取容量"):
        mod.get_capacity("C:\\")
