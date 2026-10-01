# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/linux/get_type.py。

目的（测什么）：
    验证 linux 平台 get_type 的判定顺序与规则：
    1. model 含 "sd" 或 "flash"（小写后）→ "tf_sd_card"（先于 ROTA 判定）；
    2. rota == 0（非旋转）→ "ssd"；
    3. 其余（rota == 1、rota 缺失、model 缺失）→ "hdd"。

输入：
    - 打桩 ``mod._disk_info`` 返回的 lsblk 设备字典。

期望输出：
    - "tf_sd_card" / "ssd" / "hdd"。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.linux.get_type"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        ({"rota": 0, "model": "Samsung NVMe"}, "ssd"),
        ({"rota": 1, "model": "WDC WD20EZRZ"}, "hdd"),
        ({"rota": 1, "model": "USB flash drive"}, "tf_sd_card"),
        ({"rota": 1, "model": "SD Card Reader"}, "tf_sd_card"),
        ({"rota": 1}, "hdd"),
        ({"rota": 0, "model": None}, "ssd"),
    ],
)
def test_get_type_rules(monkeypatch, info, expected):
    """rota/model 组合 → 预期设备类型。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: info)

    assert mod.get_type("/dev/sda") == expected


def test_get_type_model_containing_ssd_is_classified_as_tf_sd_card(monkeypatch):
    """记录既有规则：model 含 'SSD' 时小写后含 'sd' 子串 → 先命中 tf_sd_card。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"rota": 0, "model": "SSD 850 EVO"})

    assert mod.get_type("/dev/sda") == "tf_sd_card"
