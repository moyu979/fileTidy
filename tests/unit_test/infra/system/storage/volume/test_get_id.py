# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/volume/get_id —— 卷 ID 获取。

目的（测什么）：验证占位实现 `get_id(path)` 的输入协议：非空输入原样返回
（不做 strip）、空字符串返回 None、提示语中包含传入路径。

输入：monkeypatch 后的 `builtins.input` 应答值。

期望输出：非空应答字符串；空应答 None。
"""

from __future__ import annotations

from infra.system.storage.volume.get_id import get_id


def _feed(monkeypatch, answer: str, captured: dict | None = None) -> None:
    """把单次应答喂给 `builtins.input`，并把提示语打印到 stdout。"""

    def fake_input(prompt: str = "") -> str:
        print(prompt, end="")
        if captured is not None:
            captured["prompt"] = prompt
        return answer

    monkeypatch.setattr("builtins.input", fake_input)


def test_returns_raw_input_without_stripping(monkeypatch):
    """输入 '  V-1  ' → 原样返回（保留首尾空白）。"""
    _feed(monkeypatch, "  V-1  ")
    assert get_id("/mnt/x") == "  V-1  "


def test_empty_input_returns_none(monkeypatch):
    """输入 '' → 返回 None。"""
    _feed(monkeypatch, "")
    assert get_id("/mnt/x") is None


def test_prompt_mentions_path(monkeypatch, capsys):
    """输入 'VOL-9' → 返回 'VOL-9'，且提示语包含路径。"""
    captured: dict = {}
    _feed(monkeypatch, "VOL-9", captured)
    assert get_id("/mnt/target") == "VOL-9"
    assert "/mnt/target" in captured["prompt"]
    assert "/mnt/target" in capsys.readouterr().out
