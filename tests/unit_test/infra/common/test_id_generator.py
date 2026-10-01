# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/common/id_generator —— 时间戳 ID 生成器。

目的：验证 ID 格式、同秒自增、跨秒重置、时钟回拨时锚定最后时间戳、序号溢出
等待下一秒、并发唯一性、真实时钟格式与 CLI 入口。

输入：固定时间戳序列、构造好的内部状态、真实时钟、可选 suffix 与命令行参数。
期望输出：YYYYMMDDHHmmss_三位序号(可选 _suffix) 形式的 ID，且不产生重复。
"""

from __future__ import annotations

import re
import sys
import threading
from datetime import datetime

import pytest

from infra.common import id_generator
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


class _FakeTime:
    """id_generator 模块内 time 的替身：记录 sleep 调用，不做真实等待。"""

    def __init__(self):
        self.slept: list[float] = []

    def sleep(self, seconds):
        self.slept.append(seconds)


@pytest.fixture
def frozen_sleep(monkeypatch):
    """把 id_generator 里的 time 换成替身，让溢出用例不必真等 1 秒。

    只替换模块内的引用，不动全局 time 模块，避免影响其他代码。
    """
    fake = _FakeTime()
    monkeypatch.setattr(id_generator, "time", fake)
    return fake


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


def test_clock_rollback_anchors_last_timestamp(monkeypatch):
    """时间戳回拨（新 ts < 旧 ts）→ 沿用最后时间戳、序号继续自增，时间戳不回退。

    输入：120000 → 120001 → 回拨到 120000。
    期望输出：第三个 ID 锚定在 120001 上、序号为 001。
    """
    _freeze(monkeypatch, ["20260101120000", "20260101120001", "20260101120000"])

    ids = [generate_id() for _ in range(3)]

    assert ids == [
        "20260101120000_000",
        "20260101120001_000",
        "20260101120001_001",
    ]


def test_clock_rollback_does_not_reuse_history_sequence(monkeypatch):
    """回拨目标秒此前已用过序号 001 → 锚定后接着递增，不重发历史 ID。

    输入：120000 连发两次 → 120001 → 回拨到 120000。
    期望输出：4 个 ID 互不相同（修复前第 4 个会重发 120000_001）。
    """
    _freeze(
        monkeypatch,
        ["20260101120000", "20260101120000", "20260101120001", "20260101120000"],
    )

    ids = [generate_id() for _ in range(4)]

    assert len(set(ids)) == 4
    assert ids[3] == "20260101120001_001"


def test_timestamp_prefix_never_goes_backwards(monkeypatch):
    """连续调用中时间戳前缀单调不减，回拨也不回退。

    输入：前进、回拨、大幅回拨、再前进混合的时间戳序列。
    期望输出：各 ID 前 14 位按原序排列即为有序。
    """
    _freeze(
        monkeypatch,
        [
            "20260101120000",
            "20260101120001",
            "20260101120000",
            "20260101115959",
            "20260101120002",
        ],
    )

    ids = [generate_id() for _ in range(5)]
    prefixes = [one[:14] for one in ids]

    assert prefixes == sorted(prefixes)


def test_sequence_overflow_waits_for_next_second(monkeypatch, frozen_sleep):
    """同秒内序号已达上限 → 等待真实时钟进入下一秒并归零。

    输入：_sequence=999、last=120000，时钟先后给出 120000 与 120001。
    期望输出：ID 为 120001_000，且期间 sleep 恰好被调用一次。
    """
    monkeypatch.setattr(IDGenerator, "_sequence", 999)
    monkeypatch.setattr(IDGenerator, "_last_timestamp_str", "20260101120000")
    _freeze(monkeypatch, ["20260101120000", "20260101120001"])

    result = generate_id()

    assert result == "20260101120001_000"
    assert frozen_sleep.slept == [1]


def test_rollback_overflow_waits_for_real_clock(monkeypatch, frozen_sleep):
    """回拨且锚定时间戳上的序号已达上限 → 等真实时钟越过最后时间戳再重新计数。

    输入：_sequence=999、last=120000，时钟先给回拨值 115959、再给真实值 120001。
    期望输出：ID 为 120001_000（不会卡在锚定的 120000 上耗尽）。
    """
    monkeypatch.setattr(IDGenerator, "_sequence", 999)
    monkeypatch.setattr(IDGenerator, "_last_timestamp_str", "20260101120000")
    _freeze(monkeypatch, ["20260101115959", "20260101120001"])

    result = generate_id()

    assert result == "20260101120001_000"
    assert frozen_sleep.slept == [1]


def test_concurrent_generation_produces_unique_ids():
    """8 线程 × 100 次并发调用 → 800 个 ID 全局唯一（验证 _lock 真正互斥）。

    输入：真实时钟，8 个线程在栅栏处对齐后同时发号。
    期望输出：数量正确且无任何重复。
    """
    thread_count, per_thread = 8, 100
    barrier = threading.Barrier(thread_count)
    append_lock = threading.Lock()
    collected: list[str] = []

    def worker():
        barrier.wait()
        local = [generate_id() for _ in range(per_thread)]
        with append_lock:
            collected.extend(local)

    threads = [threading.Thread(target=worker) for _ in range(thread_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(collected) == thread_count * per_thread
    assert len(set(collected)) == len(collected)


def test_real_timestamp_matches_current_time():
    """不 mock 时钟 → _get_timestamp 返回 14 位数字串且等于当前时刻（秒级）。

    输入：真实时钟。
    期望输出：可被 %Y%m%d%H%M%S 解析，且与当前时间相差不超过 5 秒。
    """
    stamp = IDGenerator._get_timestamp()

    assert re.fullmatch(r"\d{14}", stamp)
    parsed = datetime.strptime(stamp, "%Y%m%d%H%M%S")
    assert abs((datetime.now() - parsed).total_seconds()) < 5


@pytest.mark.parametrize("suffix", ["", None])
def test_empty_or_none_suffix_omits_trailing_separator(monkeypatch, suffix):
    """suffix 为空串或 None → 只有时间戳与序号，末尾不出现多余下划线。

    输入：suffix 分别为 "" 与 None。
    期望输出：ID 形如 YYYYMMDDHHmmss_000。
    """
    _freeze(monkeypatch, ["20260101120000"])

    assert re.fullmatch(r"\d{14}_\d{3}", generate_id(suffix))


@pytest.mark.parametrize(
    ("argv", "pattern"),
    [
        (["id_generator.py"], r"\d{14}_\d{3}"),
        (["id_generator.py", "device"], r"\d{14}_\d{3}_device"),
    ],
)
def test_cli_prints_generated_id(monkeypatch, capsys, argv, pattern):
    """命令行入口 → 位置参数决定后缀，向标准输出打印一行 ID。

    输入：sys.argv 为无后缀与带 device 后缀两种。
    期望输出：打印内容与 generate_id 的格式一致。
    """
    monkeypatch.setattr(sys, "argv", argv)
    _freeze(monkeypatch, ["20260101120000"])

    id_generator.main()

    assert re.fullmatch(pattern, capsys.readouterr().out.strip())
