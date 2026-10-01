# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/volume/enum —— 卷状态枚举与状态 / 类型菜单。

目的（测什么）：
- 验证 VolumeState 的枚举取值集合；
- 验证 VolumeStateMenu 的标题、默认值、选项数量与编号映射；
- 验证 VolumeTypeMenu 的编号映射、额外支持直接输入文件系统字符串、
  空白容忍，以及无默认值时空输入返回 None。

输入：
- 枚举类本身（遍历成员核对 value）；
- 菜单输入：合法编号（"1"~"5" / "1"~"4"）、文件系统字符串（"ntfs" / "  exfat  "）、
  空串、未定义编号。

期望输出：
- 卷状态菜单编号 1~5 → 对应 VolumeState；空串 → UNKNOWN；未定义 → None；
- 卷类型菜单编号 1~4 或文件系统字符串 → 类型字符串；空串与未定义编号 → None。
"""

from __future__ import annotations

import pytest

from domain.storage.volume.enum import VolumeState, VolumeStateMenu, VolumeTypeMenu


def test_volume_state_values():
    """输入 VolumeState 各成员 → value 与领域约定一致且共 5 种状态。"""
    assert [s.value for s in VolumeState] == [
        "unknown", "healthy", "danger", "fault", "removed",
    ]


def test_volume_state_menu_metadata():
    """输入 VolumeStateMenu → 标题、默认值、选项数量与首编号符合领域约定。"""
    assert VolumeStateMenu.title == "卷状态"
    assert VolumeStateMenu.default is VolumeState.UNKNOWN
    assert len(VolumeStateMenu.options) == 5
    assert VolumeStateMenu.options[0].code == "1"


def test_volume_state_menu_prompt_and_hint():
    """输入卷状态菜单 → 提示文本含标题与全部编号，输入提示以 ": " 结尾。"""
    text = VolumeStateMenu.prompt_text()
    assert "请选择卷状态:" in text
    for code in ("1", "2", "3", "4", "5"):
        assert f"{code} —" in text
    assert VolumeStateMenu.input_hint().endswith(": ")


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("1", VolumeState.UNKNOWN),
        ("2", VolumeState.HEALTHY),
        ("3", VolumeState.DANGER),
        ("4", VolumeState.FAULT),
        ("5", VolumeState.REMOVED),
    ],
)
def test_volume_state_menu_maps_code_to_enum(code, expected):
    """输入状态菜单编号 1~5 → 返回对应 VolumeState 枚举。"""
    assert VolumeStateMenu.from_code(code) is expected


def test_volume_state_menu_default_on_empty_input():
    """输入空串 → 返回 VolumeStateMenu 默认值 VolumeState.UNKNOWN。"""
    assert VolumeStateMenu.from_code("") is VolumeState.UNKNOWN


def test_volume_type_menu_metadata():
    """输入 VolumeTypeMenu → 标题与 4 个编号选项符合领域约定，且无默认值。"""
    assert VolumeTypeMenu.title == "卷类型（文件系统类型）"
    assert [opt.code for opt in VolumeTypeMenu.options] == ["1", "2", "3", "4"]
    assert VolumeTypeMenu.default is None


@pytest.mark.parametrize(
    ("code", "expected"),
    [("1", "ntfs"), ("2", "exfat"), ("3", "fat32"), ("4", "ltfs")],
)
def test_volume_type_menu_maps_code_to_file_system(code, expected):
    """输入类型菜单编号 1~4 → 返回对应文件系统字符串。"""
    result = VolumeTypeMenu.from_code(code)
    assert result == expected
    assert isinstance(result, str)


@pytest.mark.parametrize("code", ["ntfs", "exfat", "fat32", "ltfs"])
def test_volume_type_menu_accepts_file_system_string_directly(code):
    """直接输入文件系统字符串（而非编号）→ 返回该字符串本身。"""
    assert VolumeTypeMenu.from_code(code) == code


@pytest.mark.parametrize(
    ("code", "expected"),
    [("  ntfs  ", "ntfs"), (" exfat", "exfat"), ("ltfs ", "ltfs")],
)
def test_volume_type_menu_tolerates_surrounding_whitespace(code, expected):
    """输入带首尾空白的文件系统字符串 → 去空白后仍能识别。"""
    assert VolumeTypeMenu.from_code(code) == expected


def test_volume_type_menu_empty_input_returns_none():
    """输入空串 → VolumeTypeMenu 无默认值，from_code 返回 None。"""
    assert VolumeTypeMenu.from_code("") is None
    assert VolumeTypeMenu.from_code("   ") is None


@pytest.mark.parametrize("code", ["0", "5", "ext4", "NTFS", "x"])
def test_volume_type_menu_unknown_input_returns_none(code):
    """输入未定义编号或未知文件系统串（含大小写不符）→ 返回 None。"""
    assert VolumeTypeMenu.from_code(code) is None


@pytest.mark.parametrize("code", ["0", "6", "x"])
def test_volume_state_menu_invalid_code_returns_none(code):
    """输入未定义编号 → VolumeStateMenu.from_code 返回 None。"""
    assert VolumeStateMenu.from_code(code) is None
