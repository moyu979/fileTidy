# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/device/base —— Device 实体基类。

目的（测什么）：
- 验证 Device._resolve / Device.create 按 dtype 的工厂分派（含未知类型回退基类、
  旧式 "tape-*" 兼容、子类声明 _type_key 后自动注册）；
- 验证 serial 必填校验；
- 验证 from_dict 重建、device_path 覆盖、to_snapshot 字段与 to_json 序列化；
- 验证 _parse_info 对空 / 非法 / 非对象 JSON 的兜底。

输入：
- dtype 字符串（hdd / ssd / tape / tf_sd_card / None / 未知 / "tape-lto5"）；
- 设备字段字典（完整字段、缺 serial、显式 device_path）；
- info 字符串（None / "" / "not-json" / "[1, 2]" / 合法对象 JSON）。

期望输出：
- 对应变体实例；serial 为空时 ValueError；未知 dtype 回退 Device；
- 快照含全部 9 个字段、JSON 可反序列化且中文不转义；
- 非法 info 一律解析为 {}，合法对象 JSON 解析为对应 dict。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

# 导入包即触发变体注册，保证工厂分派可用
from domain.storage.device import Device
from domain.storage.device.enum import DeviceState
from domain.storage.device.variants.hdd import HddDevice
from domain.storage.device.variants.ssd import SsdDevice
from domain.storage.device.variants.tape import TapeDevice
from domain.storage.device.variants.tf_sd import TfSdCardDevice

SNAPSHOT_KEYS = {
    "serial", "name", "type", "add_time", "last_check_time",
    "capacity", "info", "state", "device_path",
}


def _snapshot_ok(device: Device) -> dict:
    """构造一个“完整字段”的设备并返回快照字典。"""
    data = {
        "serial": "SN-001",
        "name": "测试盘",
        "type": "hdd",
        "add_time": datetime(2026, 1, 1, 8, 0, 0),
        "last_check_time": datetime(2026, 1, 2, 9, 30, 0),
        "capacity": 1_000_000_000_000,
        "info": json.dumps({"interface": "sata"}, ensure_ascii=False),
        "state": DeviceState.HEALTHY,
        "device_path": "/mnt/dev0",
    }
    return Device.from_dict(data).to_snapshot()


@pytest.mark.parametrize(
    ("dtype", "expected"),
    [
        ("hdd", HddDevice),
        ("ssd", SsdDevice),
        ("tape", TapeDevice),
        ("tf_sd_card", TfSdCardDevice),
        (None, Device),
        ("unknown_type", Device),
    ],
)
def test_create_dispatches_by_type(dtype, expected):
    """输入各 dtype → 期望返回对应变体类（未知/缺省回退基类）。"""
    device = Device.create(serial="SN-1", dtype=dtype)
    assert isinstance(device, expected)


@pytest.mark.parametrize("dtype", [None, "unknown_type"])
def test_resolve_falls_back_to_base_class(dtype):
    """输入 None 或未注册 dtype → _resolve 返回 Device 基类本身。"""
    assert Device._resolve(dtype) is Device


def test_resolve_returns_registered_variant_class():
    """输入已注册 dtype → _resolve 返回注册表中的变体类。"""
    assert Device._resolve("hdd") is HddDevice
    assert Device._registry["tape"] is TapeDevice


def test_legacy_tape_dtype_still_resolves_to_tape():
    """输入旧式 'tape-lto5' → 仍解析为 TapeDevice。"""
    device = Device.create(serial="T-1", dtype="tape-lto5")
    assert isinstance(device, TapeDevice)


def test_create_requires_serial():
    """输入空 serial → ValueError。"""
    with pytest.raises(ValueError, match="serial"):
        Device.create(serial="")


def test_create_fills_defaults():
    """只传 serial → 其余字段取默认值（空串 / None / 空列表语义）。"""
    device = Device.create(serial="SN-1")
    assert device.serial == "SN-1"
    assert device.name == ""
    assert device.dtype is None
    assert device.add_time is None
    assert device.last_check_time is None
    assert device.capacity is None
    assert device.info is None
    assert device.state is None
    assert device.device_path is None


def test_create_keeps_explicit_fields():
    """传入全部字段 → 实例属性与入参一致。"""
    device = Device.create(
        serial="SN-1",
        name="盘",
        dtype="hdd",
        add_time=datetime(2026, 1, 1),
        capacity=100,
        info="{}",
        state=DeviceState.DANGER,
        device_path="/mnt/x",
    )
    assert isinstance(device, HddDevice)
    assert (device.name, device.dtype, device.capacity) == ("盘", "hdd", 100)
    assert device.state is DeviceState.DANGER
    assert device.device_path == "/mnt/x"


def test_from_dict_roundtrip_keeps_all_fields():
    """输入完整字段字典 → from_dict 后 to_snapshot 与输入语义一致。"""
    data = {
        "serial": "SN-002",
        "name": "盘",
        "type": "ssd",
        "add_time": "2026-01-01T08:00:00",
        "last_check_time": "2026-01-02T09:30:00",
        "capacity": 512_000_000_000,
        "info": "{}",
        "state": DeviceState.HEALTHY,
        "device_path": "/mnt/sd0",
    }
    device = Device.from_dict(data)
    snapshot = device.to_snapshot()
    assert snapshot["serial"] == "SN-002"
    assert snapshot["type"] == "ssd"
    assert snapshot["capacity"] == 512_000_000_000
    assert snapshot["device_path"] == "/mnt/sd0"
    assert isinstance(device, SsdDevice)


def test_from_dict_without_serial_raises():
    """输入缺 serial 的字典 → ValueError（由 create 统一校验）。"""
    with pytest.raises(ValueError, match="serial"):
        Device.from_dict({"name": "无序列号"})


def test_from_dict_device_path_override():
    """输入字典同时显式传 device_path → 覆盖字典里的路径。"""
    device = Device.from_dict(
        {"serial": "SN-1", "device_path": "/old"},
        device_path="/new",
    )
    assert device.device_path == "/new"


def test_to_snapshot_fields_and_json():
    """输入完整设备 → 快照含全部字段且 JSON 可反序列化、中文不转义。"""
    snapshot = _snapshot_ok(Device)
    assert set(snapshot) == SNAPSHOT_KEYS
    assert snapshot["name"] == "测试盘"
    assert snapshot["add_time"] == "2026-01-01T08:00:00"
    assert snapshot["last_check_time"] == "2026-01-02T09:30:00"

    text = Device.from_dict({
        "serial": "SN-001",
        "name": "测试盘",
        "type": "hdd",
        "add_time": datetime(2026, 1, 1, 8, 0, 0),
        "last_check_time": None,
        "capacity": 1,
        "info": None,
        "state": DeviceState.HEALTHY,
    }).to_json()
    assert "测试盘" in text
    assert json.loads(text)["serial"] == "SN-001"


def test_to_snapshot_keeps_none_timestamps():
    """输入 add_time / last_check_time 为 None → 快照中保持 None（不抛错）。"""
    snapshot = Device.create(serial="SN-1").to_snapshot()
    assert snapshot["add_time"] is None
    assert snapshot["last_check_time"] is None


@pytest.mark.parametrize("info", [None, "", "not-json", "[1, 2]"])
def test_parse_info_returns_empty_for_invalid(info):
    """输入空/非法/非对象 JSON → _parse_info 返回 {}。"""
    device = Device.create(serial="SN-1", info=info)
    assert device._parse_info() == {}


def test_parse_info_valid_json():
    """输入合法 JSON 对象 → 返回 dict。"""
    device = Device.create(serial="SN-1", info='{"a": 1}')
    assert device._parse_info() == {"a": 1}


def test_custom_variant_auto_registers():
    """自定义 _type_key 子类 → 自动进入 Device._registry 并可被工厂分派。"""

    class CustomDevice(Device):
        _type_key = "custom_test_device"

    try:
        assert Device._registry["custom_test_device"] is CustomDevice
        assert isinstance(Device.create(serial="C-1", dtype="custom_test_device"), CustomDevice)
    finally:
        # 清理注册表，避免污染其他测试
        Device._registry.pop("custom_test_device", None)


def test_subclass_without_type_key_is_not_registered():
    """子类未声明 _type_key → 不进入注册表，不会被工厂分派。"""

    class UnregisteredDevice(Device):
        pass

    assert "UnregisteredDevice" not in Device._registry
    assert Device._resolve("unregistered") is Device
