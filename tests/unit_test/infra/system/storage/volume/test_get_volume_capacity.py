# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/volume/get_volume_capacity —— 卷容量人工输入。

目的（测什么）：验证占位实现 `get_volume_capacity(path)` 的整数解析协议：
先 strip 再 int、空/纯空白返回 None、非数字抛 ValueError、提示语包含路径。

输入：monkeypatch 后的 `builtins.input` 应答字符串。

期望输出：整数容量；空输入 None；非法数字抛 ValueError。
"""

from __future__ import annotations

import pytest

from infra.system.storage.volume.get_volume_capacity import get_volume_capacity


def _feed(monkeypatch, answer: str, captured: dict | None = None) -> None:
    """把单次应答喂给 `builtins.input`，并把提示语打印到 stdout。"""

    def fake_input(prompt: str = "") -> str:
        print(prompt, end="")
        if captured is not None:
            captured["prompt"] = prompt
        return answer

    monkeypatch.setattr("builtins.input", fake_input)


def test_plain_integer(monkeypatch):
    """输入 '12345' → 12345。"""
    _feed(monkeypatch, "12345")
    assert get_volume_capacity("/mnt/x") == 12345


def test_integer_with_surrounding_spaces(monkeypatch):
    """输入 '  42  ' → strip 后转换为 42。"""
    _feed(monkeypatch, "  42  ")
    assert get_volume_capacity("/mnt/x") == 42


def test_empty_input_returns_none(monkeypatch):
    """输入 '' → None。"""
    _feed(monkeypatch, "")
    assert get_volume_capacity("/mnt/x") is None


def test_whitespace_only_returns_none(monkeypatch):
    """输入 '   ' → strip 后为空 → None。"""
    _feed(monkeypatch, "   ")
    assert get_volume_capacity("/mnt/x") is None


def test_non_numeric_raises_value_error(monkeypatch):
    """输入 'abc' → 抛 ValueError（int() 解析失败）。"""
    _feed(monkeypatch, "abc")
    with pytest.raises(ValueError):
        get_volume_capacity("/mnt/x")


def test_prompt_mentions_path(monkeypatch, capsys):
    """输入 '8' → 8，且提示语包含路径。"""
    captured: dict = {}
    _feed(monkeypatch, "8", captured)
    assert get_volume_capacity("/mnt/cap") == 8
    assert "/mnt/cap" in captured["prompt"]
    assert "/mnt/cap" in capsys.readouterr().out
