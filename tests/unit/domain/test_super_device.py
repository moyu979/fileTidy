# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/super_device —— SuperDevice 实体与变体。

目的：验证按 sdtype 的工厂分派、single 类型必须恰好 1 个子设备、
serial 必填、from_dict 与快照序列化。

输入：sdtype / devices 列表等字段。
期望输出：对应变体实例；single + 0 个或 2 个子设备时抛 AssertionError。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_device.variants.raidz import RaidzSuperDevice
from domain.storage.super_device.variants.single_super_device import SingleSuperDevice


def _sd(sdtype: str | None, devices: list[str] | None = None) -> SuperDevice:
    return SuperDevice.create(
        serial="SD-1",
        name="阵列",
        sdtype=sdtype,
        need_all_devices_online=True,
        add_time=datetime(2026, 1, 1),
        last_check_time=None,
        state=SuperDeviceState.HEALTHY,
        capacity=3_000_000_000_000,
        info="{}",
        devices=devices or [],
    )


@pytest.mark.parametrize(
    ("sdtype", "expected"),
    [
        ("raidz", RaidzSuperDevice),
        ("single", SingleSuperDevice),
        (None, SuperDevice),
        ("strange", SuperDevice),
    ],
)
def test_create_dispatches_by_sdtype(sdtype, expected):
    """输入 sdtype → 返回对应变体（single 用 1 个设备构造）。"""
    devices = ["D1"] if sdtype == "single" else []
    assert isinstance(_sd(sdtype, devices), expected)


def test_single_requires_exactly_one_device():
    """single + 空设备列表 → AssertionError。"""
    with pytest.raises(AssertionError):
        _sd("single", [])


def test_create_requires_serial():
    """空 serial → ValueError。"""
    with pytest.raises(ValueError, match="serial"):
        SuperDevice.create(serial="")


def test_from_dict_and_snapshot():
    """输入字典 → 重建出 RaidzSuperDevice，devices 快照为拷贝列表。"""
    data = {
        "serial": "SD-2",
        "name": "r",
        "type": "raidz",
        "need_all_devices_online": True,
        "add_time": "2026-01-01T00:00:00",
        "last_check_time": None,
        "state": SuperDeviceState.HEALTHY,
        "capacity": 12,
        "info": "{}",
        "devices": ["D1", "D2"],
    }
    sd = SuperDevice.from_dict(data)
    assert isinstance(sd, RaidzSuperDevice)
    snapshot = sd.to_snapshot()
    assert snapshot["devices"] == ["D1", "D2"]
    snapshot["devices"].append("mutated")
    assert sd.devices == ["D1", "D2"]


def test_json_contains_chinese_and_type():
    """to_json 中文原样、type 字段为 sdtype。"""
    text = _sd("raidz", ["D1"]).to_json()
    assert "阵列" in text
    assert json.loads(text)["type"] == "raidz"
