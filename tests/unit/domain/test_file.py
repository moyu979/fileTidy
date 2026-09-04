# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/file —— NewFile 实体与事件。

目的：验证文件快照中路径归一化（Path → POSIX 字符串）、
FileRegistered / FileMoved / FileCopied 事件字段保存。

输入：字符串或 Path 形式的 from_path / now_path。
期望输出：POSIX 路径字符串、事件字段完整。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from domain.storage.file.enum import FileState
from domain.storage.file.events import FileCopied, FileMoved, FileRegistered
from domain.storage.file.new_file import NewFile


def _file(path, now_path) -> NewFile:
    return NewFile(
        sha512="a" * 128,
        md5="b" * 32,
        size=1024,
        add_time=datetime(2026, 1, 1),
        path=path,
        now_path=now_path,
        now_volume="V1",
    )


def test_snapshot_normalizes_pathlib_to_posix():
    """输入 Path 路径 → 快照中是 POSIX 字符串。"""
    nf = _file(Path("/data/src/a.txt"), Path("/mnt/vol/datas/sub/a.txt"))
    snap = nf.to_snapshot()
    assert snap["from_path"] == "/data/src/a.txt"
    assert snap["now_path"] == "/mnt/vol/datas/sub/a.txt"


def test_snapshot_keeps_default_state_and_info():
    """不传 state/info → 默认 ONLINE 与空字符串。"""
    snap = _file("x", "y").to_snapshot()
    assert snap["state"] == FileState.ONLINE
    assert snap["info"] == ""


def test_registered_event_contains_snapshot():
    """FileRegistered 保存 to_snapshot 结果。"""
    nf = _file("p", "q")
    event = FileRegistered(nf)
    assert event.file["sha512"] == nf.sha512


def test_move_copy_events_fields():
    """FileMoved / FileCopied 保存六个关键字段。"""
    moved = FileMoved("s1", "m1", "VA", "a", "VB", "b")
    assert moved.target_volume == "VB"
    assert moved.source_path == "a"

    copied = FileCopied("s1", "m1", "VA", "a", "VB", "b")
    assert copied.sha512 == "s1"
    assert copied.target_path == "b"
