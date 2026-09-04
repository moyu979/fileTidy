# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/common/merge_dir —— 目录合并。

目的：验证「已有文件跳过、缺失文件补齐」的合并规则及异常路径。

输入：临时 src/dst 目录树。
期望输出：dst 中补齐缺失文件、保留已有文件内容；非法路径抛对应异常。
"""

from __future__ import annotations

import pytest

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
