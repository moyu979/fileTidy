# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/device/variants/tf_sd —— TfSdCardDevice TF/SD 卡变体。

目的（测什么）：
- 验证 TfSdCardDevice 的注册与工厂分派（_type_key = "tf_sd_card"）；
- 验证该变体未提供 interface / form_factor / generation 读取方法
  （这些属性仅对磁盘类变体有意义）；
- 验证 check() 当前为占位实现，且未定义 set()。

输入：
- dtype="tf_sd_card" 与 serial；info JSON 文本。

期望输出：
- TfSdCardDevice 实例；get_interface / get_form_factor / get_generation 属性不存在；
- check() 返回 None；快照保留 serial 与 type。
"""

from __future__ import annotations

import pytest

from domain.storage.device import Device
from domain.storage.device.variants.tf_sd import TfSdCardDevice


def _tf_sd(serial: str = "TF-1", info: str | None = None) -> TfSdCardDevice:
    """构造一个 TfSdCardDevice 实例。"""
    return Device.create(serial=serial, dtype="tf_sd_card", info=info)  # type: ignore[return-value]


def test_tf_sd_is_registered_and_dispatched():
    """输入 dtype="tf_sd_card" → 工厂返回 TfSdCardDevice 且注册表登记该变体。"""
    assert TfSdCardDevice._type_key == "tf_sd_card"
    assert Device._registry["tf_sd_card"] is TfSdCardDevice
    assert isinstance(_tf_sd(), TfSdCardDevice)


@pytest.mark.parametrize("method", ["get_interface", "get_form_factor", "get_generation"])
def test_tf_sd_has_no_disk_metadata_getters(method):
    """输入属性名 get_interface/get_form_factor/get_generation → 该变体上不存在。"""
    assert not hasattr(TfSdCardDevice, method)
    assert not hasattr(_tf_sd(), method)


def test_tf_sd_check_is_placeholder_noop():
    """调用 check() → 占位实现返回 None 且不抛异常。"""
    assert _tf_sd().check() is None


def test_tf_sd_has_no_set_method():
    """输入属性名 set → 该变体未定义 set()（仅 check 占位）。"""
    assert not hasattr(TfSdCardDevice, "set")


def test_tf_sd_snapshot_keeps_type_and_serial():
    """输入 serial + info → 快照保留 serial 与 type="tf_sd_card"。"""
    snapshot = _tf_sd(serial="TF-9", info='{"vendor": "sandisk"}').to_snapshot()
    assert snapshot["serial"] == "TF-9"
    assert snapshot["type"] == "tf_sd_card"
    assert snapshot["info"] == '{"vendor": "sandisk"}'
