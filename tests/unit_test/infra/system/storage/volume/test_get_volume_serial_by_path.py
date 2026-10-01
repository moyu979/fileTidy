# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/volume/get_volume_serial_by_path —— 由路径取卷序列号。

目的（测什么）：验证占位实现 `get_volume_serial_by_path(path)`：输入 strip 后返回，
空输入（含纯空白）返回 None（表示不属于任何已知卷），提示语包含路径。

输入：monkeypatch 后的 `builtins.input` 应答字符串。

期望输出：非空去空白字符串；空/纯空白 None。
"""

from __future__ import annotations

from infra.system.storage.volume.get_volume_serial_by_path import (
    get_volume_serial_by_path,
)


def _feed(monkeypatch, answer: str, captured: dict | None = None) -> None:
    """把单次应答喂给 `builtins.input`，并把提示语打印到 stdout。"""

    def fake_input(prompt: str = "") -> str:
        print(prompt, end="")
        if captured is not None:
            captured["prompt"] = prompt
        return answer

    monkeypatch.setattr("builtins.input", fake_input)


def test_returns_stripped_serial(monkeypatch):
    """输入 '  V-7  ' → 返回 'V-7'。"""
    _feed(monkeypatch, "  V-7  ")
    assert get_volume_serial_by_path("/mnt/x") == "V-7"


def test_empty_input_returns_none(monkeypatch):
    """输入 '' → None。"""
    _feed(monkeypatch, "")
    assert get_volume_serial_by_path("/mnt/x") is None


def test_whitespace_only_returns_none(monkeypatch):
    """输入 '   ' → strip 后为空 → None。"""
    _feed(monkeypatch, "   ")
    assert get_volume_serial_by_path("/mnt/x") is None


def test_prompt_mentions_path(monkeypatch, capsys):
    """输入 'VOL-SN-1' → 返回该序列号，且提示语包含路径。"""
    captured: dict = {}
    _feed(monkeypatch, "VOL-SN-1", captured)
    assert get_volume_serial_by_path("/data/a.txt") == "VOL-SN-1"
    assert "/data/a.txt" in captured["prompt"]
    assert "/data/a.txt" in capsys.readouterr().out
