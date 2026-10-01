# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/unknown/is_disk.py（占位实现）。

目的（测什么）：
    unknown 平台的 is_disk 是占位实现：由用户手动回答 yes/no，
    输入去空白并转小写后属于 {"yes", "y"} 才为 True，其余一律 False。

输入：
    - 打桩 ``builtins.input`` 返回的用户输入字符串。

期望输出：
    - True / False；提示语说明可选回答。
"""

from __future__ import annotations

import importlib

import pytest

_TARGET = "infra.system.storage.device.unknown.is_disk"


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
        ("yes", True),
        ("YES ", True),
        (" y ", True),
        ("Y", True),
        ("no", False),
        ("n", False),
        ("", False),
        ("maybe", False),
        ("yes please", False),
    ],
)
def test_is_disk_manual_answer(monkeypatch, answer, expected):
    """手动确认结果 → True/False（占位行为）。"""
    mod = _mod(_TARGET)
    _patch_input(monkeypatch, answer)

    assert mod.is_disk("/dev/nope") is expected


def test_is_disk_prompt_mentions_yes_no(monkeypatch):
    """调用 is_disk → 提示语给出 yes/no 两种可选回答。"""
    mod = _mod(_TARGET)
    prompts = _patch_input(monkeypatch, "yes")

    mod.is_disk("/dev/xyz")

    assert "yes" in prompts[0]
    assert "no" in prompts[0]
