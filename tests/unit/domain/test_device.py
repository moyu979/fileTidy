# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/device —— Device 实体与设备变体。

目的：
- 验证按 dtype 的工厂分派、serial 必填校验、旧磁带 type 兼容；
- 验证 from_dict 重建、快照/JSON 序列化与 info JSON 解析兜底；
- 验证 HDD/SSD/Tape 变体对 interface / form_factor / generation 的读取规则。

输入：dtype 字符串 / 设备字段字典 / info JSON 文本。
期望输出：对应变体实例、合法快照字典、解析后的 dict（非法输入返回 {}）。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

# 导入包即触发变体注册，保证工厂分派可用
from domain.storage.device import Device
from domain.storage.device.enum import (
    DeviceFormFactor,
    DeviceInterface,
    DeviceState,
    LtoGeneration,
)
from domain.storage.device.variants.hdd import HddDevice
from domain.storage.device.variants.ssd import SsdDevice
from domain.storage.device.variants.tape import TapeDevice
from domain.storage.device.variants.tf_sd import TfSdCardDevice


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


def test_create_requires_serial():
    """输入空 serial → ValueError。"""
    with pytest.raises(ValueError, match="serial"):
        Device.create(serial="")


def test_legacy_tape_dtype_still_resolves_to_tape():
    """输入旧式 'tape-lto5' → 仍解析为 TapeDevice。"""
    device = Device.create(serial="T-1", dtype="tape-lto5")
    assert isinstance(device, TapeDevice)


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
    assert set(snapshot) == {
        "serial", "name", "type", "add_time", "last_check_time",
        "capacity", "info", "state", "device_path",
    }
    assert snapshot["name"] == "测试盘"
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


@pytest.mark.parametrize("info", [None, "", "not-json", "[1, 2]"])
def test_parse_info_returns_empty_for_invalid(info):
    """输入空/非法/非对象 JSON → _parse_info 返回 {}。"""
    device = Device.create(serial="SN-1", info=info)
    assert device._parse_info() == {}


def test_parse_info_valid_json():
    """输入合法 JSON 对象 → 返回 dict。"""
    device = Device.create(serial="SN-1", info='{"a": 1}')
    assert device._parse_info() == {"a": 1}


@pytest.mark.parametrize("cls", [HddDevice, SsdDevice])
def test_disk_interface_and_form_factor_parsing(cls):
    """SSD/HDD 输入合法/非法/缺失的 interface 与 form_factor → 对应枚举或 None。"""
    good = cls.create(
        serial="SN-1",
        dtype=cls._type_key,
        info=json.dumps({"interface": "sata", "form_factor": "2.5"}),
    )
    assert good.get_interface() == DeviceInterface.SATA
    assert good.get_form_factor() == DeviceFormFactor.TWO_POINT_FIVE

    bad = cls.create(serial="SN-2", dtype=cls._type_key, info='{"interface": "pci", "form_factor": "9.9"}')
    assert bad.get_interface() is None
    assert bad.get_form_factor() is None

    missing = cls.create(serial="SN-3", dtype=cls._type_key, info=None)
    assert missing.get_interface() is None
    assert missing.get_form_factor() is None


def test_tape_generation_parsing():
    """磁带输入合法 generation → LtoGeneration；非法/缺失 → None。"""
    good = TapeDevice.create(serial="T-1", dtype="tape", info='{"generation": "lto5"}')
    assert good.get_generation() == LtoGeneration.LTO5

    bad = TapeDevice.create(serial="T-2", dtype="tape", info='{"generation": "lto99"}')
    assert bad.get_generation() is None

    missing = TapeDevice.create(serial="T-3", dtype="tape", info=None)
    assert missing.get_generation() is None


def test_custom_variant_auto_registers():
    """自定义 _type_key 子类 → 自动进入 Device._registry 并可被工厂分派。"""

    class CustomDevice(Device):
        _type_key = "custom_test_device"

    try:
        assert isinstance(Device.create(serial="C-1", dtype="custom_test_device"), CustomDevice)
    finally:
        # 清理注册表，避免污染其他测试
        Device._registry.pop("custom_test_device", None)
