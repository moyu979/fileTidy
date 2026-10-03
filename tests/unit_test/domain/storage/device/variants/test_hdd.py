# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/device/variants/hdd —— HddDevice 机械硬盘变体。

目的（测什么）：
- 验证 HddDevice 的注册与工厂分派（_type_key = "hdd"）；
- 验证 get_interface() / get_form_factor() 从 info(JSON) 读取并校验枚举，
  对合法值返回枚举、非法值返回 None、info 缺失返回 None；
- 验证 check() / set() 当前为占位实现（返回 None，不抛错）。

输入：
- info JSON 文本：{"interface": "sata", "form_factor": "2.5"} / 非法值 / 缺失 / 非 JSON。

期望输出：
- DeviceInterface.SATA 与 DeviceFormFactor.TWO_POINT_FIVE；
- 非法或缺失时为 None；check()/set() 返回 None。
"""

from __future__ import annotations

import json

import pytest

from domain.storage.device import Device
from domain.storage.device.enum import DeviceFormFactor, DeviceInterface
from domain.storage.device.variants.hdd import HddDevice


def _hdd(serial: str = "HDD-1", info: str | None = None) -> HddDevice:
    """构造一个 HddDevice 实例。"""
    return Device.create(serial=serial, dtype="hdd", info=info)  # type: ignore[return-value]


def test_hdd_is_registered_and_dispatched():
    """输入 dtype="hdd" → 工厂返回 HddDevice 且注册表登记该变体。"""
    assert HddDevice._type_key == "hdd"
    assert Device._registry["hdd"] is HddDevice
    assert isinstance(_hdd(), HddDevice)


def test_get_interface_and_form_factor_from_info():
    """输入含合法 interface/form_factor 的 info → 返回对应枚举。"""
    device = _hdd(info=json.dumps({"interface": "sata", "form_factor": "2.5"}))
    assert device.get_interface() is DeviceInterface.SATA
    assert device.get_form_factor() is DeviceFormFactor.TWO_POINT_FIVE


@pytest.mark.parametrize("bad_info", ['{"interface": "pci", "form_factor": "9.9"}', "not-json", "[]"])
def test_get_interface_and_form_factor_invalid_returns_none(bad_info):
    """输入非法 interface/form_factor 或非 JSON → 两个 getter 均返回 None。"""
    device = _hdd(info=bad_info)
    assert device.get_interface() is None
    assert device.get_form_factor() is None


@pytest.mark.parametrize("empty_info", [None, "", "{}"])
def test_get_interface_and_form_factor_missing_returns_none(empty_info):
    """输入 info 缺失 / 空串 / 无相关键 → 两个 getter 均返回 None。"""
    device = _hdd(info=empty_info)
    assert device.get_interface() is None
    assert device.get_form_factor() is None


def test_hdd_check_and_set_are_placeholder_noops():
    """调用 check() / set() → 占位实现返回 None 且不抛异常。"""
    device = _hdd()
    assert device.check() is None
    assert device.set("interface", "sata") is None


def test_hdd_snapshot_keeps_type_and_serial():
    """输入 serial + info → 快照保留 serial 与 dtype="hdd"。"""
    snapshot = _hdd(serial="HDD-9", info='{"interface": "sas"}').to_snapshot()
    assert snapshot["serial"] == "HDD-9"
    assert snapshot["dtype"] == "hdd"
    assert snapshot["info"] == '{"interface": "sas"}'
