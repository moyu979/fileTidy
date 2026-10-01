# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/file/enum —— FileState 文件状态枚举。

目的（测什么）：
- 验证 FileState 的成员集合与取值字符串符合领域约定；
- 验证 ONLINE 是该子系统写入新文件时的默认状态（与 NewFile 默认值一致）；
- 验证枚举可按 value 反向查找（持久化层依赖这一能力）。

输入：
- FileState 枚举类本身（遍历成员、按 value 构造）。

期望输出：
- 5 个成员且 value 依次为 unknown/online/missing/damaged/removed；
- FileState("online") is FileState.ONLINE；NewFile 默认 state 为 ONLINE。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.storage.file.enum import FileState
from domain.storage.file.new_file import NewFile


def test_file_state_members_and_values():
    """输入 FileState → 成员顺序与取值符合约定。"""
    assert [s.value for s in FileState] == [
        "unknown", "online", "missing", "damaged", "removed",
    ]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("unknown", FileState.UNKNOWN),
        ("online", FileState.ONLINE),
        ("missing", FileState.MISSING),
        ("damaged", FileState.DAMAGED),
        ("removed", FileState.REMOVED),
    ],
)
def test_file_state_lookup_by_value(raw, expected):
    """输入字符串 value → FileState(value) 返回对应成员（反查能力）。"""
    assert FileState(raw) is expected


def test_file_state_lookup_rejects_unknown_value():
    """输入未定义 value → ValueError。"""
    with pytest.raises(ValueError):
        FileState("archived")


def test_default_state_on_new_file_is_online():
    """不传 state 构造 NewFile → 实例与快照中的状态均为 ONLINE。"""
    nf = NewFile(
        sha512="a",
        md5="b",
        size=1,
        add_time=None,
        path=Path("/x"),
        now_path=Path("y"),
        now_volume="V1",
    )
    assert nf.state is FileState.ONLINE
    assert nf.to_snapshot()["state"] is FileState.ONLINE
