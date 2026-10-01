# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/darwin/get_type.py。

目的（测什么）：
    验证 darwin 平台 get_type 的类型判定规则：Removable Media == "removable"
    → "tf_sd_card"；否则 Solid State == "yes" → "ssd"；其余（含字段缺失）
    一律回退 "hdd"。字段取值大小写不敏感（键名区分大小写）。

输入：
    - 打桩 ``mod._disk_info`` 返回的 diskutil info 字典。

期望输出：
    - "tf_sd_card" / "ssd" / "hdd"。

注意：darwin 包的 ``__init__`` 用同名函数覆盖了包属性，因此必须用
``importlib.import_module`` 取真正的子模块再对其 ``_disk_info`` 打桩。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.darwin.get_type"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        ({"Removable Media": "Removable", "Solid State": "Yes"}, "tf_sd_card"),
        ({"Removable Media": "REMOVABLE"}, "tf_sd_card"),
        ({"Removable Media": "No", "Solid State": "Yes"}, "ssd"),
        ({"Removable Media": "Fixed", "Solid State": "yes"}, "ssd"),
        ({"Removable Media": "No", "Solid State": "No"}, "hdd"),
        ({}, "hdd"),
    ],
)
def test_get_type_rules(monkeypatch, info, expected):
    """Removable/Solid State 字段组合 → 预期设备类型。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: info)

    assert mod.get_type("/dev/disk0") == expected


def test_get_type_forwards_path_to_disk_info(monkeypatch):
    """入参路径 → 原样传给 _disk_info，并返回其判定出的类型。"""
    mod = _mod(_TARGET)
    seen: list[str] = []

    def fake_info(path: str) -> dict[str, str]:
        seen.append(path)
        return {"Solid State": "Yes"}

    monkeypatch.setattr(mod, "_disk_info", fake_info)

    assert mod.get_type("/dev/disk3") == "ssd"
    assert seen == ["/dev/disk3"]
