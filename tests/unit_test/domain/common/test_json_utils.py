# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/common/json_utils —— parse_json_object。

目的（测什么）：
- 验证「严格版」兜底：空值 / 非法 JSON / 非对象 JSON 一律返回 {}；
- 验证合法对象 JSON 原样解析（嵌套、中文均不丢失）。

输入：
- None / 空串 / 非法 JSON 串 / 数组、数字、字符串、null、true 的 JSON / 合法对象 JSON。

期望输出：
- 只有合法对象 JSON 返回对应 dict，其余一律返回 {}。
"""

from __future__ import annotations

import pytest

from domain.common.json_utils import parse_json_object


@pytest.mark.parametrize(
    "text",
    [None, "", "not json", "[1, 2]", "123", '"abc"', "null", "true"],
)
def test_parse_json_object_returns_empty_for_unusable_input(text):
    """输入 空值 / 非法 JSON / 非对象 JSON → 期望输出 {}。"""
    assert parse_json_object(text) == {}


def test_parse_json_object_returns_dict_for_object_json():
    """输入 合法对象 JSON（含嵌套）→ 期望输出 对应 dict。"""
    assert parse_json_object('{"a": 1, "b": {"c": true}}') == {
        "a": 1,
        "b": {"c": True},
    }


def test_parse_json_object_keeps_chinese_values():
    """输入 含中文的对象 JSON → 期望输出 原样解析（不转义、不丢失）。"""
    assert parse_json_object('{"note": "中文"}') == {"note": "中文"}
