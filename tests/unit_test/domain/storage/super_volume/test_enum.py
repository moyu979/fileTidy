# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/super_volume/enum —— 超级卷状态枚举与类型 / 状态菜单。

目的（测什么）：
- 验证 SuperVolumeState 的枚举取值集合；
- 验证 SuperVolumeStateMenu 的标题、默认值、选项数量与编号映射；
- 验证 SuperVolumeTypeMenu 返回类型字符串（非枚举）、空输入回退默认 "copy"、
  未定义编号返回 None。

输入：
- 枚举类本身（遍历成员核对 value）；
- 菜单编号字符串：合法编号、空串、未定义编号（含直接输入类型名）。

期望输出：
- 枚举取值为约定的字符串常量；
- 状态菜单编号 1~5 → 对应 SuperVolumeState；空串 → UNKNOWN；未定义 → None；
- 类型菜单编号 1/2 → "copy"/"snapraid_raid5"；空串 → "copy"；未定义 → None。
"""

from __future__ import annotations

import pytest

from domain.storage.super_volume.enum import (
    SuperVolumeState,
    SuperVolumeStateMenu,
    SuperVolumeTypeMenu,
)


def test_super_volume_state_values():
    """输入 SuperVolumeState 各成员 → value 与领域约定一致且共 5 种状态。"""
    assert [s.value for s in SuperVolumeState] == [
        "unknown", "healthy", "danger", "fault", "removed",
    ]


def test_super_volume_state_menu_metadata():
    """输入 SuperVolumeStateMenu → 标题、默认值、选项数量与首编号符合领域约定。"""
    assert SuperVolumeStateMenu.title == "超级卷状态"
    assert SuperVolumeStateMenu.default is SuperVolumeState.UNKNOWN
    assert len(SuperVolumeStateMenu.options) == 5
    assert SuperVolumeStateMenu.options[0].code == "1"


def test_super_volume_state_menu_prompt_and_hint():
    """输入超级卷状态菜单 → 提示文本含标题与全部编号，输入提示以 ": " 结尾。"""
    text = SuperVolumeStateMenu.prompt_text()
    assert "请选择超级卷状态:" in text
    for code in ("1", "2", "3", "4", "5"):
        assert f"{code} —" in text
    assert SuperVolumeStateMenu.input_hint().endswith(": ")


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("1", SuperVolumeState.UNKNOWN),
        ("2", SuperVolumeState.HEALTHY),
        ("3", SuperVolumeState.DANGER),
        ("4", SuperVolumeState.FAULT),
        ("5", SuperVolumeState.REMOVED),
    ],
)
def test_super_volume_state_menu_maps_code_to_enum(code, expected):
    """输入状态菜单编号 1~5 → 返回对应 SuperVolumeState 枚举。"""
    assert SuperVolumeStateMenu.from_code(code) is expected


def test_super_volume_state_menu_default_on_empty_input():
    """输入空串 → 返回 SuperVolumeStateMenu 默认值 SuperVolumeState.UNKNOWN。"""
    assert SuperVolumeStateMenu.from_code("") is SuperVolumeState.UNKNOWN


def test_super_volume_type_menu_metadata():
    """输入 SuperVolumeTypeMenu → 默认值为 "copy" 且编号恰为 1/2。"""
    assert SuperVolumeTypeMenu.default == "copy"
    assert SuperVolumeTypeMenu.title == "超级卷类型（与系统编号一致）"
    assert [opt.code for opt in SuperVolumeTypeMenu.options] == ["1", "2"]


@pytest.mark.parametrize(
    ("code", "expected"),
    [("1", "copy"), ("2", "snapraid_raid5")],
)
def test_super_volume_type_menu_returns_type_string(code, expected):
    """输入类型菜单编号 → 返回类型字符串（不是枚举）。"""
    result = SuperVolumeTypeMenu.from_code(code)
    assert result == expected
    assert isinstance(result, str)


def test_super_volume_type_menu_default_on_empty_input():
    """输入空串 → 返回默认类型字符串 "copy"。"""
    assert SuperVolumeTypeMenu.from_code("") == "copy"


@pytest.mark.parametrize(
    ("menu", "code"),
    [
        (SuperVolumeStateMenu, "0"),
        (SuperVolumeStateMenu, "6"),
        (SuperVolumeStateMenu, "x"),
        (SuperVolumeTypeMenu, "3"),
        (SuperVolumeTypeMenu, "copy"),
    ],
)
def test_invalid_code_returns_none(menu, code):
    """输入未定义编号或直接输入类型名 → 各菜单 from_code 一律返回 None。"""
    assert menu.from_code(code) is None
