# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/common/id_generator —— 时间戳 ID 生成器。

目的：验证 ID 格式、同秒自增、跨秒重置、时钟回拨时继续递增不冲突。

输入：固定时间戳序列与可选 suffix。
期望输出：YYYYMMDDHHmmss_三位序号(可选 _suffix) 形式的 ID。
"""

from __future__ import annotations

import re

import pytest

from infra.common.id_generator import IDGenerator, generate_id


@pytest.fixture(autouse=True)
def _reset_generator(monkeypatch):
    """每个用例前重置生成器状态，避免跨用例串扰。"""
    monkeypatch.setattr(IDGenerator, "_sequence", 0)
    monkeypatch.setattr(IDGenerator, "_last_timestamp_str", "")


def _freeze(monkeypatch, timestamps: list[str]):
    """按调用次序返回固定时间戳。"""
    it = iter(timestamps)
    monkeypatch.setattr(
        IDGenerator,
        "_get_timestamp",
        staticmethod(lambda: next(it)),
    )


def test_id_format_with_and_without_suffix(monkeypatch):
    """时间戳 20260101120000 → 无后缀 id 与带后缀 id 格式正确。"""
    _freeze(monkeypatch, ["20260101120000"] * 2)
    plain = generate_id()
    suffixed = generate_id("volume")
    assert re.fullmatch(r"\d{14}_\d{3}", plain)
    assert re.fullmatch(r"\d{14}_\d{3}_volume", suffixed)


def test_sequence_increments_within_same_second(monkeypatch):
    """同一秒连续 3 次 → 序号 000/001/002。"""
    _freeze(monkeypatch, ["20260101120000"] * 3)
    ids = [generate_id() for _ in range(3)]
    assert [i[-3:] for i in ids] == ["000", "001", "002"]


def test_new_second_resets_sequence(monkeypatch):
    """时间戳推进 → 序号归零。"""
    _freeze(monkeypatch, ["20260101120000", "20260101120001"])
    first = generate_id()
    second = generate_id()
    assert first.endswith("_000")
    assert second.startswith("20260101120001")
    assert second.endswith("_000")


def test_clock_rollback_keeps_incrementing(monkeypatch):
    """时间戳回拨（新 ts < 旧 ts）→ 不归零，继续自增避免重复。"""
    _freeze(monkeypatch, ["20260101120001", "20260101120000"])
    generate_id()
    rolled = generate_id()
    assert rolled.endswith("_001")
    assert rolled.startswith("20260101120000")
