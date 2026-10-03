# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/device/variants/ssd —— SsdDevice 固态硬盘变体。

目的（测什么）：
- 验证 SsdDevice 的注册与工厂分派（_type_key = "ssd"）；
- 验证 get_interface() / get_form_factor() 从 info(JSON) 读取并校验枚举，
  M.2 长度型 form_factor（如 2280）也能正确解析；
- 验证 check() / set() 当前为占位实现（返回 None，不抛错）。

输入：
- info JSON 文本：{"interface": "nvme", "form_factor": "2280"} / 非法值 / 缺失 / 非 JSON。

期望输出：
- DeviceInterface.NVME 与 DeviceFormFactor.M2_2280；
- 非法或缺失时为 None；check()/set() 返回 None。
"""

from __future__ import annotations

import json

import pytest

from domain.storage.device import Device
from domain.storage.device.enum import DeviceFormFactor, DeviceInterface
from domain.storage.device.variants.ssd import SsdDevice


def _ssd(serial: str = "SSD-1", info: str | None = None) -> SsdDevice:
    """构造一个 SsdDevice 实例。"""
    return Device.create(serial=serial, dtype="ssd", info=info)  # type: ignore[return-value]


def test_ssd_is_registered_and_dispatched():
    """输入 dtype="ssd" → 工厂返回 SsdDevice 且注册表登记该变体。"""
    assert SsdDevice._type_key == "ssd"
    assert Device._registry["ssd"] is SsdDevice
    assert isinstance(_ssd(), SsdDevice)


def test_get_interface_and_form_factor_from_info():
    """输入含合法 interface/form_factor 的 info → 返回对应枚举。"""
    device = _ssd(info=json.dumps({"interface": "nvme", "form_factor": "2280"}))
    assert device.get_interface() is DeviceInterface.NVME
    assert device.get_form_factor() is DeviceFormFactor.M2_2280


@pytest.mark.parametrize("bad_info", ['{"interface": "pci", "form_factor": "9.9"}', "not-json", "[]"])
def test_get_interface_and_form_factor_invalid_returns_none(bad_info):
    """输入非法 interface/form_factor 或非 JSON → 两个 getter 均返回 None。"""
    device = _ssd(info=bad_info)
    assert device.get_interface() is None
    assert device.get_form_factor() is None


@pytest.mark.parametrize("empty_info", [None, "", "{}"])
def test_get_interface_and_form_factor_missing_returns_none(empty_info):
    """输入 info 缺失 / 空串 / 无相关键 → 两个 getter 均返回 None。"""
    device = _ssd(info=empty_info)
    assert device.get_interface() is None
    assert device.get_form_factor() is None


def test_ssd_check_and_set_are_placeholder_noops():
    """调用 check() / set() → 占位实现返回 None 且不抛异常。"""
    device = _ssd()
    assert device.check() is None
    assert device.set("form_factor", "2280") is None


def test_ssd_snapshot_keeps_type_and_serial():
    """输入 serial + info → 快照保留 serial 与 dtype="ssd"。"""
    snapshot = _ssd(serial="SSD-9", info='{"interface": "sata"}').to_snapshot()
    assert snapshot["serial"] == "SSD-9"
    assert snapshot["dtype"] == "ssd"
    assert snapshot["info"] == '{"interface": "sata"}'
