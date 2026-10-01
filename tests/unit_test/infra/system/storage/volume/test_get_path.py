# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/volume/get_path —— 由卷 ID 人工获取路径。

目的（测什么）：验证占位实现 `get_path(serial)` 的输入协议：非空输入原样返回
（不做 strip）、空字符串返回 None、提示语包含传入的 serial。

输入：monkeypatch 后的 `builtins.input` 应答字符串。

期望输出：非空应答字符串；空应答 None。
"""

from __future__ import annotations

from infra.system.storage.volume.get_path import get_path


def _feed(monkeypatch, answer: str, captured: dict | None = None) -> None:
    """把单次应答喂给 `builtins.input`，并把提示语打印到 stdout。"""

    def fake_input(prompt: str = "") -> str:
        print(prompt, end="")
        if captured is not None:
            captured["prompt"] = prompt
        return answer

    monkeypatch.setattr("builtins.input", fake_input)


def test_returns_raw_input_without_stripping(monkeypatch):
    """输入 ' /mnt/vol ' → 原样返回（保留首尾空白）。"""
    _feed(monkeypatch, " /mnt/vol ")
    assert get_path("S-1") == " /mnt/vol "


def test_empty_input_returns_none(monkeypatch):
    """输入 '' → None。"""
    _feed(monkeypatch, "")
    assert get_path("S-1") is None


def test_prompt_mentions_serial(monkeypatch, capsys):
    """输入 '/mnt/data' → 返回该路径，且提示语包含 serial。"""
    captured: dict = {}
    _feed(monkeypatch, "/mnt/data", captured)
    assert get_path("SERIAL-42") == "/mnt/data"
    assert "SERIAL-42" in captured["prompt"]
    assert "SERIAL-42" in capsys.readouterr().out
