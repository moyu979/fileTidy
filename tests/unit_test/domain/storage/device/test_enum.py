# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/device/enum —— 设备状态 / 接口 / 尺寸 / LTO 代次枚举与菜单。

目的（测什么）：
- 验证 DeviceState / LtoGeneration / DeviceInterface / DeviceFormFactor 的枚举取值集合；
- 验证设备相关菜单（状态 / 类型 / 接口 / 尺寸 / LTO）的编号映射，即
  「领域菜单编号 → 枚举或类型字符串」的约定；
  （尺寸菜单真实类名为 FormFactorMenu，源码中没有 DeviceFormFactorMenu）

- 验证带默认值的菜单在空输入时回退默认值，非法编号返回 None；
- 验证 DeviceTypeMenu 无默认值（空输入返回 None）。

输入：
- 各菜单的编号字符串（合法编号、空串、非法编号）；
- 枚举类本身（遍历成员核对 value）。

期望输出：
- 枚举取值为约定的字符串常量；
- 编号映射得到对应枚举成员或类型字符串；
- 非法编号 → None；空串 → 该菜单的 default。
"""

from __future__ import annotations

import pytest

from domain.storage.device.enum import (
    DeviceFormFactor,
    DeviceInterface,
    DeviceState,
    DeviceStateMenu,
    DeviceTypeMenu,
    FormFactorMenu,
    InterfaceMenu,
    LtoGeneration,
    LtoGenerationMenu,
)


def test_device_state_values():
    """输入 DeviceState 各成员 → value 与领域约定一致且共 5 种状态。"""
    assert [s.value for s in DeviceState] == [
        "unknown", "healthy", "danger", "fault", "removed",
    ]


def test_lto_generation_values_cover_lto1_to_lto9():
    """输入 LtoGeneration → 覆盖 lto1..lto9 共 9 个代次。"""
    assert [g.value for g in LtoGeneration] == [f"lto{i}" for i in range(1, 10)]


def test_device_interface_values():
    """输入 DeviceInterface → 取值集合与领域约定一致。"""
    assert {i.value for i in DeviceInterface} == {
        "sata", "sas", "nvme", "ngff", "msata", "u2", "usb",
    }


def test_device_form_factor_values():
    """输入 DeviceFormFactor → 含 2.5/3.5 英寸与 M.2 三种长度。"""
    assert {f.value for f in DeviceFormFactor} == {
        "2.5", "3.5", "2230", "2260", "2280", "22110",
    }


def test_device_state_menu_title():
    """输入 DeviceStateMenu → 标题为 "设备状态"。"""
    assert DeviceStateMenu.title == "设备状态"


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("1", DeviceState.UNKNOWN),
        ("2", DeviceState.HEALTHY),
        ("3", DeviceState.DANGER),
        ("4", DeviceState.FAULT),
        ("5", DeviceState.REMOVED),
    ],
)
def test_device_state_menu_maps_code_to_enum(code, expected):
    """输入设备状态菜单编号 1~5 → 返回对应 DeviceState 枚举。"""
    assert DeviceStateMenu.from_code(code) is expected


def test_device_state_menu_default_on_empty_input():
    """输入空串 → 返回 DeviceStateMenu 默认值 DeviceState.UNKNOWN。"""
    assert DeviceStateMenu.from_code("") is DeviceState.UNKNOWN


@pytest.mark.parametrize(
    ("code", "expected"),
    [("1", "ssd"), ("2", "hdd"), ("3", "tf_sd_card"), ("4", "tape")],
)
def test_device_type_menu_returns_type_string(code, expected):
    """输入设备类型菜单编号 → 返回类型字符串（不是枚举）。"""
    result = DeviceTypeMenu.from_code(code)
    assert result == expected
    assert isinstance(result, str)


def test_device_type_menu_has_no_default():
    """输入空串 → DeviceTypeMenu 无默认值，from_code 返回 None。"""
    assert DeviceTypeMenu.from_code("") is None


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("1", DeviceInterface.SATA),
        ("2", DeviceInterface.SAS),
        ("3", DeviceInterface.NVME),
        ("4", DeviceInterface.NGFF),
        ("5", DeviceInterface.MSATA),
        ("6", DeviceInterface.U2),
        ("7", DeviceInterface.USB),
    ],
)
def test_interface_menu_maps_code_to_enum(code, expected):
    """输入接口菜单编号 1~7 → 返回对应 DeviceInterface。"""
    assert InterfaceMenu.from_code(code) is expected


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("1", DeviceFormFactor.TWO_POINT_FIVE),
        ("2", DeviceFormFactor.THREE_POINT_FIVE),
        ("3", DeviceFormFactor.M2_2230),
        ("4", DeviceFormFactor.M2_2260),
        ("5", DeviceFormFactor.M2_2280),
        ("6", DeviceFormFactor.M2_22110),
    ],
)
def test_form_factor_menu_maps_code_to_enum(code, expected):
    """输入物理尺寸菜单编号 1~6 → 返回对应 DeviceFormFactor。"""
    assert FormFactorMenu.from_code(code) is expected


@pytest.mark.parametrize(
    ("code", "expected"),
    [(str(i), LtoGeneration(f"lto{i}")) for i in range(1, 10)],
)
def test_lto_generation_menu_maps_code_to_enum(code, expected):
    """输入 LTO 代次菜单编号 1~9 → 返回对应 LtoGeneration。"""
    assert LtoGenerationMenu.from_code(code) is expected


def test_lto_generation_menu_code_5_is_lto5():
    """输入编号 "5" → LtoGeneration.LTO5（显式回归用例）。"""
    assert LtoGenerationMenu.from_code("5") == LtoGeneration.LTO5


@pytest.mark.parametrize(
    ("menu", "code"),
    [
        (DeviceStateMenu, "9"),
        (DeviceStateMenu, "x"),
        (DeviceTypeMenu, "9"),
        (InterfaceMenu, "x"),
        (InterfaceMenu, "0"),
        (FormFactorMenu, "0"),
        (LtoGenerationMenu, "zz"),
        (LtoGenerationMenu, "10"),
    ],
)
def test_invalid_code_returns_none(menu, code):
    """输入非法编号 → 各菜单 from_code 一律返回 None。"""
    assert menu.from_code(code) is None
