# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/super_device/variants/raidz —— RaidzSuperDevice 变体。

目的（测什么）：
- 验证 RaidzSuperDevice 的注册与工厂分派（_type_key = "raidz"）；
- 验证构造函数为纯透传：入参逐字段写入实例属性；
- 验证 RAID-Z 不限制子设备数量（0 个 / 1 个 / 多个均可构造）；
- 验证快照的 type 字段为 "raidz" 且 devices 顺序保持。

输入：
- sdtype = "raidz" 与 devices 列表（0 个 / 1 个 / 3 个）。

期望输出：
- 构造出 RaidzSuperDevice 且属性与入参一致；快照 type 为 "raidz"。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_device.variants.raidz import RaidzSuperDevice


def _raidz(devices: list[str], **overrides) -> RaidzSuperDevice:
    """构造一个 RaidzSuperDevice 实例。"""
    data = {
        "serial": "RD-1",
        "name": "raidz池",
        "sdtype": "raidz",
        "need_all_devices_online": True,
        "add_time": datetime(2026, 1, 1, 8, 0, 0),
        "last_check_time": datetime(2026, 1, 2, 9, 0, 0),
        "state": SuperDeviceState.HEALTHY,
        "capacity": 24,
        "info": '{"level": "raidz1"}',
        "devices": devices,
    }
    data.update(overrides)
    return SuperDevice.create(**data)  # type: ignore[return-value]


def test_raidz_is_registered_and_dispatched():
    """输入 sdtype="raidz" → 工厂返回 RaidzSuperDevice 且注册表登记该变体。"""
    assert RaidzSuperDevice._type_key == "raidz"
    assert SuperDevice._registry["raidz"] is RaidzSuperDevice
    assert isinstance(_raidz(["D1", "D2"]), RaidzSuperDevice)


def test_raidz_constructor_passes_through_all_fields():
    """输入全部字段 → 实例属性与入参逐一一致。"""
    sd = _raidz(["D1", "D2", "D3"], name="池A", capacity=99,
                state=SuperDeviceState.DEGRADING)
    assert sd.serial == "RD-1"
    assert sd.name == "池A"
    assert sd.sdtype == "raidz"
    assert sd.need_all_devices_online is True
    assert sd.add_time == datetime(2026, 1, 1, 8, 0, 0)
    assert sd.last_check_time == datetime(2026, 1, 2, 9, 0, 0)
    assert sd.state is SuperDeviceState.DEGRADING
    assert sd.capacity == 99
    assert sd.info == '{"level": "raidz1"}'
    assert sd.devices == ["D1", "D2", "D3"]


@pytest.mark.parametrize("devices", [[], ["D1"], ["D1", "D2", "D3", "D4", "D5"]])
def test_raidz_accepts_any_device_count(devices):
    """输入 0 / 1 / 5 个子设备 → 均可构造 RaidzSuperDevice（不做数量断言）。"""
    assert _raidz(devices).devices == devices


def test_raidz_is_a_super_device():
    """输入 raidz → 实例同时是 SuperDevice（继承关系成立）。"""
    assert isinstance(_raidz(["D1"]), SuperDevice)


def test_raidz_snapshot_type_and_devices():
    """输入 raidz 实例 → 快照 type 为 "raidz"、devices 顺序不变，state 保留枚举实例。"""
    sd = _raidz(["D2", "D1"])
    snapshot = sd.to_snapshot()
    assert snapshot["type"] == "raidz"
    assert snapshot["devices"] == ["D2", "D1"]
    assert snapshot["state"] is SuperDeviceState.HEALTHY
    assert json.loads(sd.to_json())["state"] == "healthy"


def test_raidz_parse_info():
    """输入合法 info JSON → _parse_info 返回对应 dict。"""
    assert _raidz(["D1"])._parse_info() == {"level": "raidz1"}
