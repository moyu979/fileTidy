# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/volume/get_file_system —— 卷文件系统类型获取。

目的（测什么）：验证占位实现 `get_file_system(path)` 的菜单交互协议：
打印卷类型菜单、非法编号重新询问、编号或类型字符串均可返回对应文件系统。

输入：monkeypatch 后的 `builtins.input` 应答序列。

期望输出：合法编号/类型字符串返回对应字符串；非法编号打印提示后继续循环。
"""

from __future__ import annotations

from infra.system.storage.volume.get_file_system import get_file_system


def _feed(monkeypatch, *answers: str) -> None:
    """按顺序喂给 `builtins.input` 固定应答，并把提示语打印到 stdout。"""
    queue = iter(answers)

    def fake_input(prompt: str = "") -> str:
        print(prompt, end="")
        return next(queue)

    monkeypatch.setattr("builtins.input", fake_input)


def test_menu_loop_then_valid_code(monkeypatch, capsys):
    """输入 ['9','2'] → 先提示非法输入，最终返回 'exfat'。"""
    _feed(monkeypatch, "9", "2")
    assert get_file_system("/mnt/x") == "exfat"
    out = capsys.readouterr().out
    assert "请选择卷类型（文件系统类型）" in out
    assert "无效输入，请按菜单输入对应编号。" in out


def test_menu_prints_all_options(monkeypatch, capsys):
    """输入 ['1'] → 菜单文本包含全部四个选项标签。"""
    _feed(monkeypatch, "1")
    assert get_file_system("/mnt/x") == "ntfs"
    out = capsys.readouterr().out
    for label in ("NTFS", "exFAT", "FAT32", "LTFS"):
        assert label in out


def test_direct_type_string_with_whitespace(monkeypatch):
    """输入 '  fat32  '（直接类型字符串） → 去空白后返回 'fat32'。"""
    _feed(monkeypatch, "  fat32  ")
    assert get_file_system("/mnt/x") == "fat32"


def test_prompt_contains_input_hint_and_path_not_used(monkeypatch, capsys):
    """输入 ['4'] → 返回 'ltfs'，且提示含编号提示词（path 仅作参数不参与判定）。"""
    _feed(monkeypatch, "4")
    assert get_file_system("/mnt/任意路径") == "ltfs"
    assert "请输入编号 (1/2/3/4):" in capsys.readouterr().out
