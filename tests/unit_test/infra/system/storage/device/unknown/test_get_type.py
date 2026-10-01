# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/unknown/get_type.py（占位实现）。

目的（测什么）：
    unknown 平台是「无法自动探测」时的回退实现：get_type 通过 ``input()``
    让用户从菜单里手动选类型。本文件验证该占位行为：
    "1"/"2"/"3" 分别返回 "ssd"/"hdd"/"tf_sd_card"；以 "4" 开头（支持
    "45" 这类带代次输入）返回 "tape"；"None" 返回 None；其他输入抛
    ValueError。所有 input 一律用 monkeypatch 打桩，不做真实交互。

输入：
    - 打桩 ``builtins.input`` 返回的用户输入字符串。

期望输出：
    - 对应类型字符串 / None / ValueError。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.unknown.get_type"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _patch_input(monkeypatch, answer: str):
    """打桩 builtins.input，返回记录提示语列表。"""
    prompts: list[str] = []

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        return answer

    monkeypatch.setattr("builtins.input", fake_input)
    return prompts


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("1", "ssd"),
        ("2", "hdd"),
        ("3", "tf_sd_card"),
        ("4", "tape"),
        ("45", "tape"),
        ("None", None),
    ],
)
def test_get_type_manual_menu(monkeypatch, answer, expected):
    """手动菜单输入 → 对应设备类型（占位行为）。"""
    mod = _mod(_TARGET)
    _patch_input(monkeypatch, answer)

    assert mod.get_type("/dev/nope") == expected


@pytest.mark.parametrize("answer", ["9", "", "abc", "0"])
def test_get_type_invalid_input_raises(monkeypatch, answer):
    """菜单外的输入 → ValueError（消息为 "Invalid type"）。"""
    mod = _mod(_TARGET)
    _patch_input(monkeypatch, answer)

    with pytest.raises(ValueError, match="Invalid type"):
        mod.get_type("/dev/nope")


def test_get_type_prompt_mentions_os_and_options(monkeypatch):
    """调用 get_type → 提示语说明功能未实现，并列出 1:ssd 与 4:tape 选项。"""
    mod = _mod(_TARGET)
    prompts = _patch_input(monkeypatch, "1")

    mod.get_type("/dev/nope")

    assert "还没实现" in prompts[0]
    assert "1:ssd" in prompts[0]
    assert "4:tape" in prompts[0]
