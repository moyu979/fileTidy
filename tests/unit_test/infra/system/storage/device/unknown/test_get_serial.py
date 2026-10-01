# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/unknown/get_serial.py（占位实现）。

目的（测什么）：
    unknown 平台的 get_serial 是占位实现：让用户手动输入序列号，
    输入空串视为「没有序列号」返回 None，其余原样返回（不做 strip）。

输入：
    - 打桩 ``builtins.input`` 返回的用户输入字符串。

期望输出：
    - 序列号字符串 / None；提示语回显设备路径。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.unknown.get_serial"


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
        ("SN-12345", "SN-12345"),
        ("  spaced  ", "  spaced  "),
        ("", None),
    ],
)
def test_get_serial_manual_input(monkeypatch, answer, expected):
    """手动输入 → 原样返回；空串 → None（占位行为）。"""
    mod = _mod(_TARGET)
    _patch_input(monkeypatch, answer)

    assert mod.get_serial("/dev/nope") == expected


def test_get_serial_prompt_contains_path(monkeypatch):
    """调用 get_serial("/dev/xyz") → 提示语回显设备路径与未实现说明。"""
    mod = _mod(_TARGET)
    prompts = _patch_input(monkeypatch, "SN")

    mod.get_serial("/dev/xyz")

    assert "/dev/xyz" in prompts[0]
    assert "还没实现" in prompts[0]
