# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/unknown/get_capacity.py（占位实现）。

目的（测什么）：
    unknown 平台的 get_capacity 是占位实现：让用户手动输入字节数，直接
    交给 ``int()`` 转换返回。本文件验证该占位行为：合法数字串返回整数，
    非法输入抛 ValueError；提示语包含设备路径。

输入：
    - 打桩 ``builtins.input`` 返回的用户输入字符串。

期望输出：
    - 字节整数 / ValueError。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.unknown.get_capacity"


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
        ("1000000000", 1000000000),
        (" 2048 ", 2048),
        ("0", 0),
    ],
)
def test_get_capacity_manual_input(monkeypatch, answer, expected):
    """手动输入字节数 → int 结果（占位行为）。"""
    mod = _mod(_TARGET)
    _patch_input(monkeypatch, answer)

    assert mod.get_capacity("/dev/nope") == expected


@pytest.mark.parametrize("answer", ["", "abc", "1G"])
def test_get_capacity_invalid_input_raises(monkeypatch, answer):
    """非整数输入 → ValueError（由 int() 抛出）。"""
    mod = _mod(_TARGET)
    _patch_input(monkeypatch, answer)

    with pytest.raises(ValueError):
        mod.get_capacity("/dev/nope")


def test_get_capacity_prompt_contains_device_path(monkeypatch):
    """调用 get_capacity("/dev/xyz") → 提示语回显设备路径与未实现说明。"""
    mod = _mod(_TARGET)
    prompts = _patch_input(monkeypatch, "1")

    mod.get_capacity("/dev/xyz")

    assert "/dev/xyz" in prompts[0]
    assert "还没实现" in prompts[0]
