# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/volume/get_super_device_id —— 卷所属超级设备 ID。

目的（测什么）：验证占位实现 `get_super_device_id(path)`：输入先 strip 再返回，
空输入返回空字符串（不是 None），提示语包含路径。

输入：monkeypatch 后的 `builtins.input` 应答字符串。

期望输出：去首尾空白后的字符串；空输入 ''。
"""

from __future__ import annotations

from infra.system.storage.volume.get_super_device_id import get_super_device_id


def _feed(monkeypatch, answer: str, captured: dict | None = None) -> None:
    """把单次应答喂给 `builtins.input`，并把提示语打印到 stdout。"""

    def fake_input(prompt: str = "") -> str:
        print(prompt, end="")
        if captured is not None:
            captured["prompt"] = prompt
        return answer

    monkeypatch.setattr("builtins.input", fake_input)


def test_returns_stripped_value(monkeypatch):
    """输入 '  SD-1  ' → 返回 'SD-1'。"""
    _feed(monkeypatch, "  SD-1  ")
    assert get_super_device_id("/mnt/x") == "SD-1"


def test_empty_input_returns_empty_string(monkeypatch):
    """输入 '' → 返回 ''（空字符串而非 None）。"""
    _feed(monkeypatch, "")
    result = get_super_device_id("/mnt/x")
    assert result == ""
    assert result is not None


def test_prompt_mentions_path_and_field(monkeypatch, capsys):
    """输入 'SD-9' → 返回 'SD-9'，且提示语包含路径与字段名。"""
    captured: dict = {}
    _feed(monkeypatch, "SD-9", captured)
    assert get_super_device_id("/mnt/sd") == "SD-9"
    assert "/mnt/sd" in captured["prompt"]
    assert "super_device_id" in capsys.readouterr().out
