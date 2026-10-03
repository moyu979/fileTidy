# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/super_device/variants/single_super_device —— 单设备超级设备变体。

目的（测什么）：
- 验证 SingleSuperDevice 的注册与工厂分派（_type_key = "single"）；
- 验证构造约束：devices 列表长度必须恰为 1，否则抛 AssertionError；
- 验证构造函数为透传：入参逐字段写入实例属性；
- 验证快照的 type 字段为 "single"。

输入：
- sdtype = "single" 与 devices 列表（0 个 / 1 个 / 2 个）。

期望输出：
- 恰好 1 个设备时构造成功；0 个或 2 个时抛 AssertionError。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_device.variants.single_super_device import SingleSuperDevice


def _single(devices: list[str], **overrides) -> SingleSuperDevice:
    """构造一个 SingleSuperDevice 实例。"""
    data = {
        "serial": "SG-1",
        "name": "单盘",
        "sdtype": "single",
        "need_all_devices_online": False,
        "add_time": datetime(2026, 1, 1, 8, 0, 0),
        "last_check_time": None,
        "state": SuperDeviceState.UNKNOWN,
        "capacity": 4_000_000_000_000,
        "info": "{}",
        "devices": devices,
    }
    data.update(overrides)
    return SuperDevice.create(**data)  # type: ignore[return-value]


def test_single_is_registered_and_dispatched():
    """输入 sdtype="single" + 1 个设备 → 工厂返回 SingleSuperDevice。"""
    assert SingleSuperDevice._type_key == "single"
    assert SuperDevice._registry["single"] is SingleSuperDevice
    assert isinstance(_single(["D1"]), SingleSuperDevice)


def test_single_constructor_passes_through_all_fields():
    """输入全部字段 → 实例属性与入参逐一一致。"""
    sd = _single(["HDD-9"], name="单盘A", capacity=7, state=SuperDeviceState.DANGER)
    assert sd.serial == "SG-1"
    assert sd.name == "单盘A"
    assert sd.sdtype == "single"
    assert sd.need_all_devices_online is False
    assert sd.add_time == datetime(2026, 1, 1, 8, 0, 0)
    assert sd.last_check_time is None
    assert sd.state is SuperDeviceState.DANGER
    assert sd.capacity == 7
    assert sd.devices == ["HDD-9"]


@pytest.mark.parametrize("devices", [[], ["D1", "D2"], ["D1", "D2", "D3"]])
def test_single_requires_exactly_one_device(devices):
    """输入 非 REMOVED + 0 个 / 2 个 / 3 个设备 → 抛 AssertionError（长度必须为 1）。"""
    with pytest.raises(AssertionError):
        _single(devices)


def test_single_allows_zero_devices_when_removed():
    """输入 state=REMOVED + 0 个设备 → 构造成功（软删会释放子项，0 子项合法）。"""
    sd = _single([], state=SuperDeviceState.REMOVED)
    assert sd.devices == []
    assert sd.is_removed() is True


def test_single_accepts_exactly_one_device():
    """输入恰好 1 个设备 → 构造成功且 devices 原样保存。"""
    assert _single(["ONLY-1"]).devices == ["ONLY-1"]


def test_single_is_a_super_device():
    """输入 single → 实例同时是 SuperDevice（继承关系成立）。"""
    assert isinstance(_single(["D1"]), SuperDevice)


def test_single_snapshot_type():
    """输入 single 实例 → 快照 type 为 "single"，state 保留枚举实例（JSON 时才转字符串）。"""
    sd = _single(["D1"])
    snapshot = sd.to_snapshot()
    assert snapshot["sdtype"] == "single"
    assert snapshot["devices"] == ["D1"]
    assert snapshot["state"] is SuperDeviceState.UNKNOWN
    assert json.loads(sd.to_json())["state"] == "unknown"
