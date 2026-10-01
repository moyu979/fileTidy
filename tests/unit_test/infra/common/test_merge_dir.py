# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/common/merge_dir —— 目录合并。

目的：验证「已有文件跳过、缺失文件补齐」的合并规则、异常路径，以及空目录、
隐藏文件、dst 多余文件保留、拷贝中途失败时不回滚（非原子）等边界行为。

输入：临时 src/dst 目录树；需要制造拷贝失败时用 shutil 替身。
期望输出：dst 中补齐缺失文件、保留既有内容与多余文件；非法路径抛对应异常。
"""

from __future__ import annotations

import os
import shutil

import pytest

from infra.common import merge_dir as merge_dir_module
from infra.common.merge_dir import merge_dir


def test_merge_copies_missing_and_skips_existing(tmp_path):
    """src 有 a(新) 与 keep(已存在) → 只补 a，keep 原内容不变。"""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    (src / "sub").mkdir(parents=True)
    (src / "a.txt").write_text("new", encoding="utf-8")
    (src / "keep.txt").write_text("from-src", encoding="utf-8")

    dst.mkdir()
    (dst / "keep.txt").write_text("from-dst", encoding="utf-8")

    merge_dir(src, dst)

    assert (dst / "a.txt").read_text(encoding="utf-8") == "new"
    assert (dst / "keep.txt").read_text(encoding="utf-8") == "from-dst"
    assert (dst / "sub").is_dir()


def test_merge_nested_tree(tmp_path):
    """src 深层目录 → dst 中递归创建并拷贝文件。"""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    dst.mkdir()
    (src / "x" / "y").mkdir(parents=True)
    (src / "x" / "y" / "f.bin").write_bytes(b"\x01\x02")

    merge_dir(src, dst)

    assert (dst / "x" / "y" / "f.bin").read_bytes() == b"\x01\x02"


def test_missing_src_raises(tmp_path):
    """src 不存在 → FileNotFoundError。"""
    dst = tmp_path / "dst"
    dst.mkdir()
    with pytest.raises(FileNotFoundError):
        merge_dir(tmp_path / "nope", dst)


def test_src_is_file_raises(tmp_path):
    """src 是文件 → NotADirectoryError。"""
    src = tmp_path / "a.txt"
    dst = tmp_path / "dst"
    src.write_text("x", encoding="utf-8")
    dst.mkdir()
    with pytest.raises(NotADirectoryError):
        merge_dir(src, dst)


def test_dst_missing_raises(tmp_path):
    """dst 不存在 → NotADirectoryError。"""
    src = tmp_path / "src"
    src.mkdir()
    with pytest.raises(NotADirectoryError):
        merge_dir(src, tmp_path / "no-dst")


def test_does_not_overwrite_different_content(tmp_path):
    """同名但内容与 mtime 都不同 → 仍然跳过，dst 那份分毫不动。

    输入：src/same.txt 为 "from-src"（mtime=1000000）；
          dst/same.txt 为 "from-dst"（mtime=2000000）。
    期望输出：dst 内容与 mtime 均保持原值（copy2 未被调用）。
    """
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    src_file = src / "same.txt"
    dst_file = dst / "same.txt"
    src_file.write_text("from-src", encoding="utf-8")
    dst_file.write_text("from-dst", encoding="utf-8")
    (src / "new.txt").write_text("new", encoding="utf-8")
    os.utime(src_file, (1_000_000, 1_000_000))
    os.utime(dst_file, (2_000_000, 2_000_000))

    merge_dir(src, dst)

    # 同名的跳过（含 mtime 不动），缺失的照常补齐——证明合并确实跑过
    assert dst_file.read_text(encoding="utf-8") == "from-dst"
    assert int(dst_file.stat().st_mtime) == 2_000_000
    assert (dst / "new.txt").read_text(encoding="utf-8") == "new"


def test_extra_files_in_dst_are_kept(tmp_path):
    """dst 中 src 没有的文件与目录 → 不被删除。

    输入：src 只有 a.txt，dst 另有 extra/keep.bin。
    期望输出：dst 中 a.txt 被补上，extra/keep.bin 原样保留。
    """
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "a.txt").write_text("a", encoding="utf-8")
    (dst / "extra").mkdir(parents=True)
    (dst / "extra" / "keep.bin").write_bytes(b"\x00keep")

    merge_dir(src, dst)

    assert (dst / "a.txt").read_text(encoding="utf-8") == "a"
    assert (dst / "extra" / "keep.bin").read_bytes() == b"\x00keep"


def test_empty_directories_are_created(tmp_path):
    """src 中的空目录（含深层空目录）→ 在 dst 中同样建出且仍为空。

    输入：src 有 empty/deep/，两级都不含文件。
    期望输出：dst 中 empty/deep 存在且其中没有任何文件。
    """
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    (src / "empty" / "deep").mkdir(parents=True)
    dst.mkdir()

    merge_dir(src, dst)

    assert (dst / "empty" / "deep").is_dir()
    assert not [path for path in (dst / "empty").rglob("*") if path.is_file()]


def test_hidden_files_are_merged(tmp_path):
    """点开头的隐藏文件与隐藏目录 → 同样参与合并（rglob("*") 会匹配它们）。

    输入：src 有 .hidden 与 .config/x.ini，dst 为空目录。
    期望输出：两者都出现在 dst 中且内容一致。
    """
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    (src / ".config").mkdir(parents=True)
    (src / ".hidden").write_text("h", encoding="utf-8")
    (src / ".config" / "x.ini").write_text("x", encoding="utf-8")
    dst.mkdir()

    merge_dir(src, dst)

    assert (dst / ".hidden").read_text(encoding="utf-8") == "h"
    assert (dst / ".config" / "x.ini").read_text(encoding="utf-8") == "x"


class _FailingShutil:
    """shutil 替身：第 fail_on 次 copy2 调用抛 OSError，其余委托真实实现。"""

    def __init__(self, fail_on: int) -> None:
        self.fail_on = fail_on
        self.calls = 0

    def copy2(self, src, dst):
        self.calls += 1
        if self.calls == self.fail_on:
            raise OSError(f"模拟拷贝失败: {src}")
        return shutil.copy2(src, dst)


def test_partial_copy_failure_does_not_roll_back(tmp_path, monkeypatch):
    """第 2 次拷贝失败 → 异常向上抛，已拷成功的文件不被回滚（非原子）。

    输入：src 有 a/b/c.txt，替身在第 2 次 copy2 时抛 OSError。
    期望输出：抛 OSError；dst 只剩已成功的 a.txt，b/c.txt 不存在。
    """
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    for name in ("a.txt", "b.txt", "c.txt"):
        (src / name).write_text(name, encoding="utf-8")
    dst.mkdir()

    monkeypatch.setattr(merge_dir_module, "shutil", _FailingShutil(fail_on=2))

    with pytest.raises(OSError):
        merge_dir(src, dst)

    assert (dst / "a.txt").read_text(encoding="utf-8") == "a.txt"
    assert not (dst / "b.txt").exists()
    assert not (dst / "c.txt").exists()
