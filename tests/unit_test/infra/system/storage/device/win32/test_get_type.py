# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/win32/get_type.py。

目的（测什么）：
    验证 win32 平台 get_type 基于 wmic 的 MediaType/Size 判定类型：
    - 找不到磁盘（``_get_drive_by_path`` 为 None）→ ValueError；
    - MediaType 含 "ssd"/"solid" → "ssd"；
    - MediaType 含 "external"/"removable" 且容量 < 256GB → "tf_sd_card"；
    - 其余（含 MediaType 缺失）→ "hdd"。

输入：
    - 打桩 ``mod._get_drive_by_path`` 返回的 diskdrive 字典。

期望输出：
    - "ssd" / "hdd" / "tf_sd_card"；找不到磁盘时 ValueError。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.win32.get_type"

_GB = 1024**3


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def test_get_type_raises_when_drive_not_found(monkeypatch):
    """_get_drive_by_path 返回 None → ValueError（消息含路径）。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_get_drive_by_path", lambda path: None)

    with pytest.raises(ValueError, match="无法获取类型"):
        mod.get_type("E:\\")


@pytest.mark.parametrize(
    ("drive", "expected"),
    [
        ({"MediaType": "SSD", "Size": 500 * _GB}, "ssd"),
        ({"MediaType": "Solid State Drive", "Size": 500 * _GB}, "ssd"),
        ({"MediaType": "Fixed hard disk media", "Size": 2000 * _GB}, "hdd"),
        ({"MediaType": "", "Size": 2000 * _GB}, "hdd"),
        ({"Size": 2000 * _GB}, "hdd"),
        ({"MediaType": "Removable Media", "Size": 64 * _GB}, "tf_sd_card"),
        ({"MediaType": "External", "Size": 64 * _GB}, "tf_sd_card"),
        ({"MediaType": "Removable Media", "Size": 1000 * _GB}, "hdd"),
    ],
)
def test_get_type_rules(monkeypatch, drive, expected):
    """MediaType/Size 组合 → 预期设备类型。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_get_drive_by_path", lambda path: drive)

    assert mod.get_type("E:\\") == expected


def test_get_type_removable_with_wmic_string_size_raises_type_error(monkeypatch):
    """可移动介质 + 字符串 Size（真实 wmic 输出）→ 比较 str 与 int 抛 TypeError。

    真实 ``_get_drive_by_path`` 返回的 Size 来自 CSV 文本（str），
    故 removable/external 分支在当前实现下会抛 TypeError（记录既有行为）。
    """
    mod = _mod(_TARGET)
    monkeypatch.setattr(
        mod, "_get_drive_by_path",
        lambda path: {"MediaType": "Removable Media", "Size": "68719476736"},
    )

    with pytest.raises(TypeError):
        mod.get_type("E:\\")
