# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/common/menu —— 通用菜单基类 _Menu。

目的（测什么）：
- 验证 _Menu.prompt_text() 生成的菜单文本包含标题与全部选项编号；
- 验证 _Menu.input_hint() 生成的输入提示（有默认值 / 无默认值两条分支）；
- 验证 _Menu.from_code() 的编号映射、value_type 转换、空输入回退 default、
  非法输入返回 None，以及首尾空白容忍。

输入：
- 自定义 _Menu 子类（枚举型带默认值 / 字符串型无默认值）的类方法调用；
- 菜单编号字符串：合法编号、空串、纯空白串、未定义编号。

期望输出：
- prompt_text 返回多行文本，首行为 "请选择<标题>:"，其余每行含 "编号 — 标签 (描述)"；
- input_hint 返回 "请输入编号 (1/2/...): "，有默认值时附带 "直接回车默认 <首编号>"；
- from_code 合法编号 → 对应值（value_type 非空时返回枚举实例）；
  空串 → default；未定义编号 → None。
"""

from __future__ import annotations

import enum

import pytest

from domain.common.menu import _Menu, _MenuOption


class _DemoColor(enum.Enum):
    """演示用枚举。"""

    RED = "red"
    BLUE = "blue"


class _DemoEnumMenu(_Menu):
    """枚举型演示菜单：有默认值，value_type 会把字符串转成枚举。"""

    title = "演示颜色"
    value_type = _DemoColor
    default = _DemoColor.RED
    options = [
        _MenuOption("1", _DemoColor.RED, "RED", "红色（默认）"),
        _MenuOption("2", _DemoColor.BLUE, "BLUE", "蓝色"),
    ]


class _DemoStrMenu(_Menu):
    """字符串型演示菜单：无默认值，from_code 直接返回选项 value。"""

    title = "演示类型"
    options = [
        _MenuOption("1", "alpha", "Alpha", "甲种"),
        _MenuOption("2", "beta", "Beta", "乙种"),
    ]


def test_prompt_text_contains_title_and_every_code():
    """输入 _DemoEnumMenu → prompt_text 含标题行与全部编号。"""
    text = _DemoEnumMenu.prompt_text()
    lines = text.splitlines()
    assert lines[0] == "请选择演示颜色:"
    assert "  1 — RED (红色（默认）)" in lines
    assert "  2 — BLUE (蓝色)" in lines


def test_prompt_text_reenumerates_lazily_built_code_map():
    """输入 _DemoEnumMenu → 调用 prompt_text 后 _code_map 已被惰性构建。"""
    _DemoEnumMenu._code_map = None
    _DemoEnumMenu.prompt_text()
    assert _DemoEnumMenu._code_map == {"1": _DemoColor.RED, "2": _DemoColor.BLUE}
    _DemoEnumMenu._code_map = None


def test_input_hint_lists_codes_and_colon_suffix():
    """输入无默认值菜单 → 提示串只列编号并以 ": " 结尾。"""
    hint = _DemoStrMenu.input_hint()
    assert hint == "请输入编号 (1/2): "


def test_input_hint_with_default_appends_default_hint():
    """输入带默认值菜单 → 提示串附带 "直接回车默认 <首个编号>"。"""
    hint = _DemoEnumMenu.input_hint()
    assert hint == "请输入编号 (1/2，直接回车默认 1): "


def test_from_code_maps_code_to_enum_instance():
    """输入编号 "2" → 返回 value_type 转换后的枚举实例。"""
    assert _DemoEnumMenu.from_code("2") is _DemoColor.BLUE


def test_from_code_maps_code_to_raw_value_when_no_value_type():
    """输入无 value_type 菜单的编号 "2" → 直接返回原始字符串值。"""
    assert _DemoStrMenu.from_code("2") == "beta"


def test_from_code_tolerates_surrounding_whitespace():
    """输入 "  1 " → 去空白后仍能正确映射。"""
    assert _DemoEnumMenu.from_code("  1 ") is _DemoColor.RED


def test_from_code_empty_input_returns_default():
    """输入空串 / 纯空白 → 返回菜单 default（无 default 时为 None）。"""
    assert _DemoEnumMenu.from_code("") is _DemoColor.RED
    assert _DemoEnumMenu.from_code("   ") is _DemoColor.RED
    assert _DemoStrMenu.from_code("") is None


@pytest.mark.parametrize("code", ["9", "0", "x", "RED", "-1"])
def test_from_code_unknown_input_returns_none(code):
    """输入未定义编号或非编号文本 → 返回 None。"""
    assert _DemoEnumMenu.from_code(code) is None
