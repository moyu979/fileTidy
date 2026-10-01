# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/unknown/get_healthy.py（占位实现）。

目的（测什么）：
    unknown 平台的 get_healthy 是占位实现：让用户输入与 ``list(DeviceState)``
    下标一一对应的整数。本文件验证该占位行为：0–4 分别映射
    UNKNOWN/HEALTHY/DANGER/FAULT/REMOVED；越界或非整数抛 ValueError；
    提示语列出全部状态编码。

输入：
    - 打桩 ``builtins.input`` 返回的用户输入字符串。

期望输出：
    - DeviceState 枚举成员 / ValueError。
"""

from __future__ import annotations

import importlib

import pytest

from domain.storage.device.enum import DeviceState

_TARGET = "infra.system.storage.device.unknown.get_healthy"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _patch_input(monkeypatch, answer: str):
    """打桩 builtins.input，返回记录提示语列表。"""
    prompts: list[str] = []

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        return answer

    monkeypatch.setattr("builtins.input", fake_input)
    return prompts


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("0", DeviceState.UNKNOWN),
        ("1", DeviceState.HEALTHY),
        ("2", DeviceState.DANGER),
        ("3", DeviceState.FAULT),
        ("4", DeviceState.REMOVED),
        (" 3 ", DeviceState.FAULT),
    ],
)
def test_get_healthy_index_maps_to_device_state(monkeypatch, answer, expected):
    """下标输入 → 与 DeviceState 定义顺序一致的枚举成员（占位行为）。"""
    mod = _mod(_TARGET)
    _patch_input(monkeypatch, answer)

    assert mod.get_healthy("/dev/nope") is expected


@pytest.mark.parametrize("answer", ["5", "-1", "99"])
def test_get_healthy_out_of_range_raises(monkeypatch, answer):
    """越界下标 → ValueError（消息含合法区间）。"""
    mod = _mod(_TARGET)
    _patch_input(monkeypatch, answer)

    with pytest.raises(ValueError, match="健康状态编码须在"):
        mod.get_healthy("/dev/nope")


@pytest.mark.parametrize("answer", ["", "abc"])
def test_get_healthy_non_integer_raises(monkeypatch, answer):
    """非整数输入 → ValueError（由 int() 抛出）。"""
    mod = _mod(_TARGET)
    _patch_input(monkeypatch, answer)

    with pytest.raises(ValueError):
        mod.get_healthy("/dev/nope")


def test_get_healthy_prompt_lists_all_states(monkeypatch):
    """调用 get_healthy("/dev/xyz") → 提示语含路径与 DeviceState 全部「序号 — 名称」对照。"""
    mod = _mod(_TARGET)
    prompts = _patch_input(monkeypatch, "0")

    mod.get_healthy("/dev/xyz")

    text = prompts[0]
    assert "/dev/xyz" in text
    for index, state in enumerate(DeviceState):
        assert f"{index} — {state.name}" in text
