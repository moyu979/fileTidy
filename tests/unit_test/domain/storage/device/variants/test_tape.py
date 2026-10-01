# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/device/variants/tape —— TapeDevice 磁带变体。

目的（测什么）：
- 验证 TapeDevice 的注册与工厂分派（_type_key = "tape"，兼容旧式 "tape-lto5"）；
- 验证 get_generation() 从 info(JSON) 的 "generation" 键读取并校验 LtoGeneration；
- 验证 check() / set() 当前为占位实现（返回 None，不抛错）；
- 验证模块级 TAPE_CAPACITY_BYTES 容量映射表的键集合。

输入：
- info JSON 文本：{"generation": "lto5"} / 非法代次 / 缺失 / 非 JSON；
- 旧式 dtype "tape-lto5"。

期望输出：
- LtoGeneration.LTO5；非法或缺失时为 None；旧式 dtype 仍构造出 TapeDevice。
"""

from __future__ import annotations

import pytest

from domain.storage.device import Device
from domain.storage.device.enum import LtoGeneration
from domain.storage.device.variants.tape import TAPE_CAPACITY_BYTES, TapeDevice


def _tape(serial: str = "T-1", info: str | None = None, dtype: str = "tape") -> TapeDevice:
    """构造一个 TapeDevice 实例。"""
    return Device.create(serial=serial, dtype=dtype, info=info)  # type: ignore[return-value]


def test_tape_is_registered_and_dispatched():
    """输入 dtype="tape" → 工厂返回 TapeDevice 且注册表登记该变体。"""
    assert TapeDevice._type_key == "tape"
    assert Device._registry["tape"] is TapeDevice
    assert isinstance(_tape(), TapeDevice)


def test_legacy_dtype_with_generation_suffix_still_builds_tape():
    """输入旧式 dtype="tape-lto5" → 仍构造 TapeDevice 实例。"""
    assert isinstance(_tape(dtype="tape-lto5"), TapeDevice)


@pytest.mark.parametrize(
    ("generation", "expected"),
    [
        ("lto1", LtoGeneration.LTO1),
        ("lto5", LtoGeneration.LTO5),
        ("lto6", LtoGeneration.LTO6),
        ("lto9", LtoGeneration.LTO9),
    ],
)
def test_get_generation_returns_enum_for_valid_value(generation, expected):
    """输入合法 generation → 返回对应 LtoGeneration 枚举。"""
    assert _tape(info=f'{{"generation": "{generation}"}}').get_generation() is expected


@pytest.mark.parametrize("bad_info", ['{"generation": "lto99"}', '{"generation": ""}', "not-json", "[1]"])
def test_get_generation_invalid_returns_none(bad_info):
    """输入非法/空 generation 或非 JSON → 返回 None。"""
    assert _tape(info=bad_info).get_generation() is None


@pytest.mark.parametrize("empty_info", [None, "", "{}"])
def test_get_generation_missing_returns_none(empty_info):
    """输入 info 缺失 / 空串 / 无 generation 键 → 返回 None。"""
    assert _tape(info=empty_info).get_generation() is None


def test_tape_check_and_set_are_placeholder_noops():
    """调用 check() / set() → 占位实现返回 None 且不抛异常。"""
    device = _tape()
    assert device.check() is None
    assert device.set("generation", "lto5") is None


def test_tape_capacity_table_covers_declared_generations():
    """输入容量映射表 → 含 lto1 / lto5 / lto6 且值为正数。"""
    assert set(TAPE_CAPACITY_BYTES) == {"lto1", "lto5", "lto6"}
    assert all(value > 0 for value in TAPE_CAPACITY_BYTES.values())
    assert TAPE_CAPACITY_BYTES["lto5"] == 1024 * 1024 * 1024 * 1000 * 1.5


def test_tape_snapshot_keeps_type_and_serial():
    """输入 serial + dtype="tape" → 快照保留 serial 与 type="tape"。"""
    snapshot = _tape(serial="T-9").to_snapshot()
    assert snapshot["serial"] == "T-9"
    assert snapshot["type"] == "tape"
