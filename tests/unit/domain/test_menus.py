# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/common/menu 与各领域菜单。

目的：
- 验证通用 _Menu 的 prompt_text / input_hint / from_code（含默认值、非法输入）；
- 验证 Device / Volume / SuperDevice / SuperVolume 各类菜单的编号映射，
  以及 VolumeTypeMenu 支持直接输入文件系统字符串。

输入：菜单编号 / 空串 / 非法串。
期望输出：对应枚举或类型字符串；非法输入返回 None。
"""

from __future__ import annotations

import pytest

from domain.storage.device.enum import (
    DeviceState,
    DeviceStateMenu,
    DeviceTypeMenu,
    FormFactorMenu,
    InterfaceMenu,
    LtoGeneration,
    LtoGenerationMenu,
)
from domain.storage.super_device.enum import SuperDeviceStateMenu, SuperDeviceTypeMenu
from domain.storage.super_volume.enum import SuperVolumeStateMenu, SuperVolumeTypeMenu
from domain.storage.volume.enum import VolumeState, VolumeStateMenu, VolumeTypeMenu


def test_prompt_text_contains_options():
    """调用 prompt_text → 输出包含标题与全部编号。"""
    text = DeviceStateMenu.prompt_text()
    assert "设备状态" in text
    for code in ("1", "2", "3", "4", "5"):
        assert f"{code} —" in text


def test_input_hint_lists_codes():
    """调用 input_hint → 包含 1/2/... 与冒号。"""
    hint = DeviceStateMenu.input_hint()
    assert "1/2/3/4/5" in hint
    assert hint.endswith(": ")


@pytest.mark.parametrize(
    ("menu", "code", "expected"),
    [
        (DeviceStateMenu, "1", "unknown"),
        (DeviceStateMenu, "5", "removed"),
        (VolumeStateMenu, "2", "healthy"),
        (SuperDeviceStateMenu, "4", "degrading"),
        (SuperVolumeStateMenu, "5", "removed"),
    ],
)
def test_state_menus_map_code_to_enum(menu, code, expected):
    """状态菜单输入编号 → 返回枚举（字符串断言取其 value）。"""
    result = menu.from_code(code)
    assert result is not None
    assert result.value == expected


def test_type_menus_return_strings():
    """类型菜单返回字符串而非枚举。"""
    assert DeviceTypeMenu.from_code("1") == "ssd"
    assert DeviceTypeMenu.from_code("4") == "tape"
    assert SuperDeviceTypeMenu.from_code("2") == "raidz"
    assert SuperVolumeTypeMenu.from_code("1") == "copy"
    assert SuperVolumeTypeMenu.from_code("2") == "snapraid_raid5"


def test_default_on_empty_input():
    """空串输入 → 返回菜单 default（SuperDeviceTypeMenu 默认 single）。"""
    assert SuperDeviceTypeMenu.from_code("") == "single"
    assert DeviceStateMenu.from_code("") == DeviceState.UNKNOWN


def test_invalid_code_returns_none():
    """非法编号 → None。"""
    assert DeviceStateMenu.from_code("9") is None
    assert InterfaceMenu.from_code("x") is None
    assert FormFactorMenu.from_code("0") is None
    assert LtoGenerationMenu.from_code("zz") is None


@pytest.mark.parametrize("code", ["1", "ntfs", "exfat", "fat32", "ltfs"])
def test_volume_type_menu_accepts_number_or_fs_string(code):
    """VolumeTypeMenu 支持编号或直接输入文件系统字符串。"""
    result = VolumeTypeMenu.from_code(code)
    assert result is not None
    assert result in {"ntfs", "exfat", "fat32", "ltfs"}


def test_lto_generation_menu():
    """LTO 菜单编号 5 → LtoGeneration.LTO5。"""
    assert LtoGenerationMenu.from_code("5") == LtoGeneration.LTO5
