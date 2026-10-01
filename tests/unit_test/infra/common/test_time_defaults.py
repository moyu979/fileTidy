"""单测：infra/common/time_defaults —— 「尚未巡检」的占位时间常量。

目的（测什么）：验证 `LAST_CHECK_TIME_ORIGIN` 的类型、取值、无时区（naive UTC）语义，
       以及它确实是「纪元起点」而非当前时间（用作缺省值的判别依据）。
输入：模块常量本身，以及当前时间 `datetime.utcnow()` 作对照。
期望输出：常量是 `datetime` 实例，等于 `datetime(1970, 1, 1, 0, 0, 0)`，
       `tzinfo is None`、微秒为 0，且恒小于当前时间。
"""

from __future__ import annotations

from datetime import datetime

from infra.common.time_defaults import LAST_CHECK_TIME_ORIGIN


def test_origin_is_datetime_instance():
    """输入 模块常量 LAST_CHECK_TIME_ORIGIN → 期望输出 是 datetime 实例。"""
    assert isinstance(LAST_CHECK_TIME_ORIGIN, datetime)


def test_origin_equals_unix_epoch():
    """输入 模块常量 → 期望输出 精确等于 datetime(1970, 1, 1, 0, 0, 0)。"""
    assert LAST_CHECK_TIME_ORIGIN == datetime(1970, 1, 1, 0, 0, 0)
    assert (
        LAST_CHECK_TIME_ORIGIN.year,
        LAST_CHECK_TIME_ORIGIN.month,
        LAST_CHECK_TIME_ORIGIN.day,
        LAST_CHECK_TIME_ORIGIN.hour,
        LAST_CHECK_TIME_ORIGIN.minute,
        LAST_CHECK_TIME_ORIGIN.second,
        LAST_CHECK_TIME_ORIGIN.microsecond,
    ) == (1970, 1, 1, 0, 0, 0, 0)


def test_origin_is_naive_utc():
    """输入 模块常量 → 期望输出 tzinfo 为 None（与项目 datetime.utcnow 风格一致）。"""
    assert LAST_CHECK_TIME_ORIGIN.tzinfo is None
    assert LAST_CHECK_TIME_ORIGIN.utcoffset() is None


def test_origin_is_in_the_past_relative_to_now():
    """输入 当前 utcnow 与常量比较 → 期望输出 当前时间严格晚于纪元起点。"""
    assert datetime.utcnow() > LAST_CHECK_TIME_ORIGIN


def test_origin_isoformat_is_epoch_without_timezone_suffix():
    """输入 模块常量 → 期望输出 isoformat 为 '1970-01-01T00:00:00'（无时区后缀）。"""
    assert LAST_CHECK_TIME_ORIGIN.isoformat() == "1970-01-01T00:00:00"
