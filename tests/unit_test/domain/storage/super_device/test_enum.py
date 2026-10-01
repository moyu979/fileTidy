# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/super_device/enum —— 超级设备状态 / 关联状态枚举与菜单。

目的（测什么）：
- 验证 SuperDeviceState 与 RelationState 的枚举取值集合；
- 验证 SuperDeviceStateMenu 的标题、默认值、选项数量与编号映射；
- 验证 SuperDeviceTypeMenu 返回类型字符串（非枚举）、空输入回退默认 "single"、
  未定义编号返回 None。

输入：
- 枚举类本身（遍历成员核对 value）；
- 菜单编号字符串：合法编号、空串、未定义编号（含直接输入类型名）。

期望输出：
- 枚举取值为约定的字符串常量；
- 状态菜单编号 1~6 → 对应 SuperDeviceState；空串 → UNKNOWN；未定义 → None；
- 类型菜单编号 1/2 → "single"/"raidz"；空串 → "single"；未定义 → None。
"""

from __future__ import annotations

import pytest

from domain.storage.super_device.enum import (
    RelationState,
    SuperDeviceState,
    SuperDeviceStateMenu,
    SuperDeviceTypeMenu,
)


def test_super_device_state_values():
    """输入 SuperDeviceState 各成员 → value 与领域约定一致且共 6 种状态。"""
    assert [s.value for s in SuperDeviceState] == [
        "unknown", "healthy", "danger", "degrading", "fault", "removed",
    ]


def test_relation_state_values():
    """输入 RelationState → 取值仅 using / unused 两种。"""
    assert [s.value for s in RelationState] == ["using", "unused"]


def test_super_device_state_menu_metadata():
    """输入 SuperDeviceStateMenu → 标题、默认值、选项数量与首编号符合领域约定。"""
    assert SuperDeviceStateMenu.title == "超级设备状态"
    assert SuperDeviceStateMenu.default is SuperDeviceState.UNKNOWN
    assert len(SuperDeviceStateMenu.options) == 6
    assert SuperDeviceStateMenu.options[0].code == "1"


def test_super_device_state_menu_prompt_and_hint():
    """输入超级设备状态菜单 → 提示文本含标题与全部编号，输入提示以 ": " 结尾。"""
    text = SuperDeviceStateMenu.prompt_text()
    assert "请选择超级设备状态:" in text
    for code in ("1", "2", "3", "4", "5", "6"):
        assert f"{code} —" in text
    assert "1/2/3/4/5/6" in SuperDeviceStateMenu.input_hint()
    assert SuperDeviceStateMenu.input_hint().endswith(": ")


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("1", SuperDeviceState.UNKNOWN),
        ("2", SuperDeviceState.HEALTHY),
        ("3", SuperDeviceState.DANGER),
        ("4", SuperDeviceState.DEGRADING),
        ("5", SuperDeviceState.FAULT),
        ("6", SuperDeviceState.REMOVED),
    ],
)
def test_super_device_state_menu_maps_code_to_enum(code, expected):
    """输入状态菜单编号 1~6 → 返回对应 SuperDeviceState 枚举。"""
    assert SuperDeviceStateMenu.from_code(code) is expected


def test_super_device_state_menu_default_on_empty_input():
    """输入空串 → 返回 SuperDeviceStateMenu 默认值 SuperDeviceState.UNKNOWN。"""
    assert SuperDeviceStateMenu.from_code("") is SuperDeviceState.UNKNOWN


def test_super_device_type_menu_metadata():
    """输入 SuperDeviceTypeMenu → 默认值为 "single" 且编号恰为 1/2。"""
    assert SuperDeviceTypeMenu.default == "single"
    assert SuperDeviceTypeMenu.title == "超级设备类型（与系统编号一致）"
    assert [opt.code for opt in SuperDeviceTypeMenu.options] == ["1", "2"]


@pytest.mark.parametrize(("code", "expected"), [("1", "single"), ("2", "raidz")])
def test_super_device_type_menu_returns_type_string(code, expected):
    """输入类型菜单编号 → 返回类型字符串（不是枚举）。"""
    result = SuperDeviceTypeMenu.from_code(code)
    assert result == expected
    assert isinstance(result, str)


def test_super_device_type_menu_default_on_empty_input():
    """输入空串 → 返回默认类型字符串 "single"。"""
    assert SuperDeviceTypeMenu.from_code("") == "single"


@pytest.mark.parametrize(
    ("menu", "code"),
    [
        (SuperDeviceStateMenu, "0"),
        (SuperDeviceStateMenu, "7"),
        (SuperDeviceStateMenu, "x"),
        (SuperDeviceTypeMenu, "3"),
        (SuperDeviceTypeMenu, "raidz"),
    ],
)
def test_invalid_code_returns_none(menu, code):
    """输入未定义编号或直接输入类型名 → 各菜单 from_code 一律返回 None。"""
    assert menu.from_code(code) is None
