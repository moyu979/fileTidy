# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/super_device/base —— SuperDevice 实体基类。

目的（测什么）：
- 验证 SuperDevice._resolve / SuperDevice.create 按 sdtype 的工厂分派
  （含 None 与未注册类型回退基类、子类声明 _type_key 后自动注册）；
- 验证 serial 必填校验；
- 验证 create 的默认值填充与显式字段透传；
- 验证 from_dict 重建、to_snapshot 字段集合与 devices 快照为拷贝、to_json 序列化；
- 验证 _parse_info 对空 / 非法 / 非对象 JSON 的兜底。

输入：
- sdtype 字符串（"raidz" / "single" / None / 未注册的 "strange"）；
- 超级设备字段字典（完整字段、只含 serial、缺 serial）；
- info 字符串（None / "" / "not-json" / "[1, 2]" / 合法对象 JSON）。

期望输出：
- 对应变体实例；serial 为空时 ValueError；未知 sdtype 回退 SuperDevice 基类；
- 快照含全部 10 个字段、JSON 可反序列化且中文不转义；
- 非法 info 一律解析为 {}，合法对象 JSON 解析为对应 dict。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

# 导入包即触发变体注册，保证工厂分派可用
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_device.variants.raidz import RaidzSuperDevice
from domain.storage.super_device.variants.single_super_device import SingleSuperDevice

SNAPSHOT_KEYS = {
    "serial", "name", "type", "need_all_devices_online", "add_time",
    "last_check_time", "state", "capacity", "info", "devices",
}


def _sd(sdtype: str | None = None, devices: list[str] | None = None, **overrides) -> SuperDevice:
    """构造一个 SuperDevice 实例，未显式给出的字段使用固定测试值。"""
    data = {
        "serial": "SD-1",
        "name": "阵列",
        "sdtype": sdtype,
        "need_all_devices_online": True,
        "add_time": datetime(2026, 1, 1),
        "last_check_time": None,
        "state": SuperDeviceState.HEALTHY,
        "capacity": 3_000_000_000_000,
        "info": "{}",
        "devices": devices if devices is not None else [],
    }
    data.update(overrides)
    return SuperDevice.create(**data)


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
    """输入 sdtype（raidz / single / None / 未注册）→ 返回对应变体类，未注册回退基类。"""
    devices = ["D1"] if sdtype == "single" else []
    assert isinstance(_sd(sdtype, devices), expected)


def test_resolve_returns_registered_variant_class():
    """输入已注册 sdtype → _resolve 返回注册表中的变体类本身。"""
    assert SuperDevice._resolve("raidz") is RaidzSuperDevice
    assert SuperDevice._resolve("single") is SingleSuperDevice


def test_resolve_falls_back_to_base_class():
    """输入 None 或未注册 sdtype → _resolve 返回 SuperDevice 基类本身。"""
    assert SuperDevice._resolve(None) is SuperDevice
    assert SuperDevice._resolve("strange") is SuperDevice


def test_registry_contains_builtin_variants():
    """导入包后 → 注册表包含 single / raidz 两个内置变体且指向对应类。"""
    assert {"single", "raidz"} <= set(SuperDevice._registry)
    assert SuperDevice._registry["raidz"] is RaidzSuperDevice
    assert SuperDevice._registry["single"] is SingleSuperDevice


def test_subclass_without_type_key_is_not_registered():
    """定义未声明 _type_key 的子类 → 不进入注册表，_resolve 仍回退基类。"""
    class _AnonymousSuperDevice(SuperDevice):
        """未声明 _type_key 的临时子类。"""

    assert "anonymous_super_device" not in SuperDevice._registry
    assert SuperDevice._resolve("anonymous_super_device") is SuperDevice


def test_create_requires_serial():
    """输入空 serial → ValueError。"""
    with pytest.raises(ValueError, match="serial"):
        SuperDevice.create(serial="")


def test_from_dict_without_serial_raises():
    """输入缺 serial 的字典 → ValueError（由 create 统一校验）。"""
    with pytest.raises(ValueError, match="serial"):
        SuperDevice.from_dict({"name": "无序列号"})


def test_create_fills_defaults():
    """只传 serial → 其余字段取默认值（空串 / None / False / 空列表）。"""
    sd = SuperDevice.create(serial="SD-1")
    assert sd.serial == "SD-1"
    assert sd.name == ""
    assert sd.sdtype is None
    assert sd.need_all_devices_online is False
    assert sd.add_time is None
    assert sd.last_check_time is None
    assert sd.state is None
    assert sd.capacity is None
    assert sd.info is None
    assert sd.devices == []
    assert type(sd) is SuperDevice


def test_create_keeps_explicit_fields():
    """传入全部字段 → 实例属性与入参一致，且类型为 raidz 变体。"""
    sd = _sd("raidz", ["D1", "D2"], name="池", capacity=100,
             state=SuperDeviceState.DEGRADING)
    assert isinstance(sd, RaidzSuperDevice)
    assert (sd.name, sd.sdtype, sd.capacity) == ("池", "raidz", 100)
    assert sd.state is SuperDeviceState.DEGRADING
    assert sd.need_all_devices_online is True
    assert sd.devices == ["D1", "D2"]
    assert sd.add_time == datetime(2026, 1, 1)
    assert sd.last_check_time is None


def test_from_dict_rebuilds_variant_and_copies_devices_snapshot():
    """输入完整字典 → 重建 RaidzSuperDevice，且 devices 快照是拷贝（改快照不影响实体）。"""
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


def test_from_dict_defaults_for_missing_optional_fields():
    """输入只有 serial 的字典 → 可选字段取默认值且回退基类。"""
    sd = SuperDevice.from_dict({"serial": "SD-3"})
    assert type(sd) is SuperDevice
    assert sd.name == ""
    assert sd.sdtype is None
    assert sd.need_all_devices_online is False
    assert sd.devices == []


def test_to_snapshot_fields_and_json():
    """输入完整实体 → 快照含全部 10 个字段，JSON 可反序列化且中文不转义。"""
    sd = _sd("raidz", ["D1"], name="阵列")
    snapshot = sd.to_snapshot()
    assert set(snapshot) == SNAPSHOT_KEYS
    assert snapshot["type"] == "raidz"
    assert snapshot["add_time"] == "2026-01-01T00:00:00"
    assert snapshot["last_check_time"] is None

    payload = json.loads(sd.to_json())
    assert "阵列" in sd.to_json()
    assert payload["type"] == "raidz"
    assert payload["state"] == "healthy"


def test_to_snapshot_keeps_none_timestamps_for_base_instance():
    """输入只有 serial 的实体 → 快照时间字段为 None 且不抛错。"""
    snapshot = SuperDevice.create(serial="SD-1").to_snapshot()
    assert snapshot["add_time"] is None
    assert snapshot["last_check_time"] is None


@pytest.mark.parametrize("info", [None, "", "not-json", "[1, 2]"])
def test_parse_info_returns_empty_for_invalid(info):
    """输入空 / 非法 JSON / 非对象 JSON → _parse_info 返回 {}。"""
    assert _sd("raidz", ["D1"], info=info)._parse_info() == {}


def test_parse_info_returns_dict_for_valid_object():
    """输入合法对象 JSON → _parse_info 返回对应 dict。"""
    assert _sd("raidz", ["D1"], info='{"k": 1}')._parse_info() == {"k": 1}
