# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/operation_log/operation_log —— 事件日志。

目的：验证 EventLogger 按“events-YYYY-MM.log”落盘并可读回；
log_event / load_events 在未初始化时抛 RuntimeError。

输入：含 Enum / datetime 字段的事件对象与临时日志目录。
期望输出：日志行可反序列化且字段完整；未初始化时报 RuntimeError。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

import pytest

import infra.operation_log.operation_log as oplog
from infra.operation_log.operation_log import (
    EventLogger,
    load_events,
    log_event,
    setup_event_logger,
)


class _FakeConfig:
    """只提供 log.operation_log_path 的最小配置替身。"""

    def __init__(self, path) -> None:
        self.path = path

    def __getitem__(self, key):
        assert key == "log"
        return {"operation_log_path": str(self.path)}


class _SampleState(Enum):
    OK = "ok"


class _SampleEvent:
    def __init__(self):
        self.serial = "SN-1"
        self.state = _SampleState.OK
        self.when = datetime(2026, 1, 1, 0, 0, 0)


def _reset_logger():
    oplog._logger = None


def test_event_logger_writes_and_loads(tmp_path):
    """写入事件 → 生成 events-*.log，load_all 读回完整记录。"""
    logger = EventLogger(_FakeConfig(tmp_path))
    logger.log(_SampleEvent())

    records = logger.load_all()
    assert len(records) == 1
    record = records[0]
    assert record["type"] == "_SampleEvent"
    assert record["data"]["serial"] == "SN-1"
    assert record["data"]["state"] == "ok"
    assert "T00:00:00" in record["data"]["when"]


def test_log_file_path_contains_current_month(tmp_path):
    """日志文件名形如 events-<YYYY>-<MM>.log。"""
    EventLogger(_FakeConfig(tmp_path)).log(_SampleEvent())
    now = datetime.utcnow()
    expected = tmp_path / f"events-{now.year}-{now.month:02d}.log"
    assert expected.is_file()


def test_global_api_requires_setup(tmp_path, monkeypatch):
    """未初始化时 log_event/load_events → RuntimeError。"""
    _reset_logger()
    monkeypatch.setattr(oplog, "_logger", None)
    with pytest.raises(RuntimeError):
        log_event(_SampleEvent())
    with pytest.raises(RuntimeError):
        load_events()


def test_global_api_roundtrip(tmp_path):
    """setup 后 log_event + load_events 完整往返。"""
    try:
        _reset_logger()
        setup_event_logger(_FakeConfig(tmp_path))
        log_event(_SampleEvent())
        records = load_events()
        assert len(records) == 1
        assert records[0]["type"] == "_SampleEvent"
    finally:
        _reset_logger()
