# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/common/mixins —— JsonSerializableMixin。

目的（测什么）：
- 验证 to_json() / __str__() 的序列化行为（中文不转义、枚举取 value）；
- 验证 _json_default() 对 Enum 的转换与对未知类型的 TypeError；
- 验证 _ts() 对 None / datetime / 无 isoformat 普通值的处理分支。

输入：
- 自定义 JsonSerializableMixin 子类实例（字段为 None / datetime / Enum / 普通对象）；
- 直接调用 _json_default / _ts 的边界值。

期望输出：
- to_json 返回可被 json.loads 解析的字符串，__str__ 与 to_json 完全一致；
- 枚举序列化为其 value；不可序列化对象抛 TypeError；
- _ts(None) → None；datetime → isoformat 字符串；无 isoformat 的普通值原样返回。
"""

from __future__ import annotations

import enum
import json
from datetime import datetime

import pytest

from domain.common.mixins import JsonSerializableMixin


class _Color(enum.Enum):
    """演示用枚举。"""

    RED = "red"


class _Sample(JsonSerializableMixin):
    """最小可序列化实体：仅用于驱动 Mixin 的公共方法。"""

    def __init__(self, name: str = "", ts=None, state=None) -> None:
        self.name = name
        self.ts = ts
        self.state = state

    def to_snapshot(self) -> dict:
        return {"name": self.name, "ts": self._ts(self.ts), "state": self.state}


def test_to_json_serializes_enum_as_value():
    """输入 state=_Color.RED → JSON 中该字段为 "red"。"""
    payload = json.loads(_Sample(name="s", state=_Color.RED).to_json())
    assert payload["state"] == "red"


def test_to_json_keeps_chinese_unescaped():
    """输入中文名称 → JSON 文本中原样保留中文（ensure_ascii=False）。"""
    text = _Sample(name="测试名称").to_json()
    assert "测试名称" in text
    assert json.loads(text)["name"] == "测试名称"


def test_str_equals_to_json():
    """调用 str(实例) → 与 to_json() 输出完全一致。"""
    sample = _Sample(name="s", ts=datetime(2026, 1, 1, 8, 0, 0))
    assert str(sample) == sample.to_json()


def test_to_json_raises_type_error_for_unserializable_value():
    """输入不可序列化的普通对象 → json.dumps 经 _json_default 抛 TypeError。"""
    with pytest.raises(TypeError, match="not JSON serializable"):
        _Sample(state=object()).to_json()


def test_json_default_converts_enum_to_value():
    """直接调用 _json_default(枚举成员) → 返回其 value。"""
    assert _Sample()._json_default(_Color.RED) == "red"


def test_json_default_rejects_non_enum():
    """直接调用 _json_default(非枚举) → 抛 TypeError 并带上类型名。"""
    with pytest.raises(TypeError, match="int is not JSON serializable"):
        _Sample()._json_default(1)


@pytest.mark.parametrize("value", [None, "", 0, 1.5, {"a": 1}, [1, 2]])
def test_ts_passthrough_for_values_without_isoformat(value):
    """输入 None / 无 isoformat 的普通值 → 原样返回（None 亦返回 None）。"""
    assert _Sample()._ts(value) == value


def test_ts_formats_datetime_as_isoformat():
    """输入 datetime → 返回其 ISO 格式字符串。"""
    moment = datetime(2026, 1, 2, 9, 30, 0)
    assert _Sample()._ts(moment) == "2026-01-02T09:30:00"


def test_snapshot_uses_formatted_timestamp():
    """输入带 datetime 的实体 → to_snapshot 的时间字段已是 ISO 字符串。"""
    snapshot = _Sample(ts=datetime(2026, 2, 1, 12, 0, 0)).to_snapshot()
    assert snapshot["ts"] == "2026-02-01T12:00:00"
