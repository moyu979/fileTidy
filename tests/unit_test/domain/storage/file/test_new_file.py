# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/file/new_file —— NewFile 实体。

目的（测什么）：
- 验证 to_snapshot() 的路径归一化（Path → POSIX 字符串、str 原样保留）；
- 验证 state / info 的默认值（ONLINE、空串）与 add_time 的 ISO 格式化；
- 验证 to_json() 序列化（中文不转义、FileState 取 value）；
- 顺带覆盖同包的 file/events.py（纯事件载体，按仓库约定不单独建测试文件）：
  FileRegistered / FileMoved / FileCopied 的字段保存。

输入：
- 字符串或 Path 形式的 path / now_path，以及 sha512 / md5 / size / add_time；
- 事件构造参数（六元组）。

期望输出：
- 快照 9 个字段齐全，路径为 POSIX 字符串，时间为 ISO 字符串；
- 事件对象保存快照或原始字段。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from domain.storage.file.enum import FileState
from domain.storage.file.events import FileCopied, FileMoved, FileRegistered
from domain.storage.file.new_file import NewFile

SNAPSHOT_KEYS = {
    "sha512", "md5", "size", "add_time",
    "from_path", "now_volume", "now_path", "state", "info",
}


def _file(path, now_path, **overrides) -> NewFile:
    """构造一个 NewFile 实例。"""
    data = {
        "sha512": "a" * 128,
        "md5": "b" * 32,
        "size": 1024,
        "add_time": datetime(2026, 1, 1),
        "path": path,
        "now_path": now_path,
        "now_volume": "V1",
    }
    data.update(overrides)
    return NewFile(**data)


def test_snapshot_normalizes_pathlib_to_posix():
    """输入 Path 路径 → 快照中是 POSIX 字符串。"""
    nf = _file(Path("/data/src/a.txt"), Path("/mnt/vol/datas/sub/a.txt"))
    snap = nf.to_snapshot()
    assert snap["from_path"] == "/data/src/a.txt"
    assert snap["now_path"] == "/mnt/vol/datas/sub/a.txt"


def test_snapshot_keeps_string_paths_unchanged():
    """输入 str 路径 → 快照原样保留（不做任何转换）。"""
    snap = _file("/data/src/b.txt", "datas/b.txt").to_snapshot()
    assert snap["from_path"] == "/data/src/b.txt"
    assert snap["now_path"] == "datas/b.txt"


def test_snapshot_keeps_default_state_and_info():
    """不传 state/info → 默认 ONLINE 与空字符串。"""
    snap = _file("x", "y").to_snapshot()
    assert snap["state"] == FileState.ONLINE
    assert snap["info"] == ""


def test_snapshot_contains_all_fields_and_iso_time():
    """输入完整字段 → 快照键集合齐全且 add_time 为 ISO 字符串。"""
    snap = _file("x", "y").to_snapshot()
    assert set(snap) == SNAPSHOT_KEYS
    assert snap["add_time"] == "2026-01-01T00:00:00"
    assert snap["sha512"] == "a" * 128
    assert snap["md5"] == "b" * 32
    assert snap["size"] == 1024
    assert snap["now_volume"] == "V1"


def test_snapshot_accepts_explicit_state_and_info():
    """传入 state=FileState.MISSING 与 info → 快照使用显式值。"""
    snap = _file("x", "y", state=FileState.MISSING, info='{"note": "丢失"}').to_snapshot()
    assert snap["state"] is FileState.MISSING
    assert snap["info"] == '{"note": "丢失"}'


def test_to_json_is_parsable_and_keeps_chinese():
    """调用 to_json() → JSON 可反序列化，中文不转义，枚举取 value。"""
    text = _file("/数据/源.txt", "datas/源.txt", info="备注").to_json()
    payload = json.loads(text)
    assert "数据" in text
    assert payload["from_path"] == "/数据/源.txt"
    assert payload["state"] == "online"
    assert payload["info"] == "备注"


def test_registered_event_contains_snapshot():
    """输入 NewFile → FileRegistered.file 保存其 to_snapshot 结果。"""
    nf = _file("p", "q")
    event = FileRegistered(nf)
    assert event.file["sha512"] == nf.sha512
    assert event.file == nf.to_snapshot()


def test_moved_event_stores_all_fields():
    """输入六元组 → FileMoved 保存源/目标卷与路径。"""
    moved = FileMoved("s1", "m1", "VA", "a", "VB", "b")
    assert (moved.sha512, moved.md5) == ("s1", "m1")
    assert moved.source_volume == "VA"
    assert moved.source_path == "a"
    assert moved.target_volume == "VB"
    assert moved.target_path == "b"


def test_copied_event_stores_all_fields():
    """输入六元组 → FileCopied 保存源/目标卷与路径。"""
    copied = FileCopied("s1", "m1", "VA", "a", "VB", "b")
    assert copied.sha512 == "s1"
    assert copied.md5 == "m1"
    assert copied.source_volume == "VA"
    assert copied.source_path == "a"
    assert copied.target_volume == "VB"
    assert copied.target_path == "b"
