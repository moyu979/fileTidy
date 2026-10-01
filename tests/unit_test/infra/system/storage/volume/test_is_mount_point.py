# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/volume/is_mount_point —— 挂载点人工确认。

目的（测什么）：验证占位实现 `is_mount_point(path)` 的 y/n 判定协议：
仅小写 'y' 判定为 True，其余输入（含大写 'Y'）均为 False，提示语包含待判路径。

输入：monkeypatch 后的 `builtins.input` 应答字符串。

期望输出：'y' → True；'n' / 'Y' / 空串 → False。
"""

from __future__ import annotations

from infra.system.storage.volume.is_mount_point import is_mount_point


def _feed(monkeypatch, answer: str, captured: dict | None = None) -> None:
    """把单次应答喂给 `builtins.input`，并把提示语打印到 stdout。"""

    def fake_input(prompt: str = "") -> str:
        print(prompt, end="")
        if captured is not None:
            captured["prompt"] = prompt
        return answer

    monkeypatch.setattr("builtins.input", fake_input)


def test_lowercase_y_is_true(monkeypatch):
    """输入 'y' → True。"""
    _feed(monkeypatch, "y")
    assert is_mount_point("/mnt/x") is True


def test_lowercase_n_is_false(monkeypatch):
    """输入 'n' → False。"""
    _feed(monkeypatch, "n")
    assert is_mount_point("/mnt/x") is False


def test_uppercase_y_is_false(monkeypatch):
    """输入 'Y' → False（实现为大小写敏感比较）。"""
    _feed(monkeypatch, "Y")
    assert is_mount_point("/mnt/x") is False


def test_empty_answer_is_false(monkeypatch):
    """输入 '' → False。"""
    _feed(monkeypatch, "")
    assert is_mount_point("/mnt/x") is False


def test_prompt_mentions_path(monkeypatch, capsys):
    """输入 'y' → 提示语中出现待判断路径。"""
    captured: dict = {}
    _feed(monkeypatch, "y", captured)
    assert is_mount_point("/mnt/check-me") is True
    assert "/mnt/check-me" in captured["prompt"]
    assert "/mnt/check-me" in capsys.readouterr().out
