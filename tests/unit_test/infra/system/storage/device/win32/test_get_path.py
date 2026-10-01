# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/win32/get_path.py（含 _common._wmic CSV 解析）。

目的（测什么）：
    1. get_path 按序列号查 wmic 的 diskdrive → Index，再查 partition →
       logicaldisk assoc，返回形如 "C:" 的盘符；任一环节为空返回 None；
    2. 私有 ``_common._wmic`` 的 CSV 解析：丢弃首列 Node、首行为表头、空行；
       结果不足两行返回 []；命令非零退出抛 RuntimeError（不单独建测试文件，
       断言并入本文件）。

输入：
    - 打桩 ``mod._wmic`` 的分步响应序列；
    - 打桩 ``_common.subprocess`` 的假 wmic CSV 输出。

期望输出：
    - 盘符字符串或 None；CSV 解析为键值字典列表。
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

_TARGET = "infra.system.storage.device.win32.get_path"
_COMMON = "infra.system.storage.device.win32._common"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _seq_wmic(responses: list):
    """按顺序弹出响应的假 _wmic，同时记录命令行。"""
    calls: list[str] = []

    def fake(cmd: str):
        calls.append(cmd)
        return responses.pop(0)

    return fake, calls


# ── get_path ─────────────────────────────────────────────────────────


def test_get_path_resolves_drive_letter(monkeypatch):
    """序列号 → Index → partition → assoc → 返回盘符。"""
    mod = _mod(_TARGET)
    fake, calls = _seq_wmic([
        [{"Index": "1"}],
        [{"DeviceID": "\\\\?\\disk#1"}],
        [{"Dependent": "C:"}],
    ])
    monkeypatch.setattr(mod, "_wmic", fake)

    assert mod.get_path("SN-1") == "C:"
    assert 'SerialNumber="SN-1"' in calls[0]
    assert "DiskIndex=1" in calls[1]


@pytest.mark.parametrize(
    "responses",
    [
        [[]],                                        # 序列号查不到磁盘
        [[{"Index": "1"}], []],                      # 没有分区
        [[{"Index": "1"}], [{"DeviceID": "x"}], []],  # 没有关联盘符
        [[{"Index": "1"}], [{"DeviceID": "x"}], [{"Dependent": "not-a-drive"}]],
    ],
)
def test_get_path_returns_none(monkeypatch, responses):
    """任一级查询为空或找不到形如 "C:" 的值 → None。"""
    mod = _mod(_TARGET)
    fake, _ = _seq_wmic(responses)
    monkeypatch.setattr(mod, "_wmic", fake)

    assert mod.get_path("SN-1") is None


def test_get_path_skips_non_drive_letter_values(monkeypatch):
    """关联行含 "AA" 与 "D:" → 跳过非盘符值并返回 "D:"。"""
    mod = _mod(_TARGET)
    fake, _ = _seq_wmic([
        [{"Index": "0"}],
        [{"DeviceID": "\\\\?\\disk#0"}],
        [{"Antecedent": "AA", "Dependent": "D:"}],
    ])
    monkeypatch.setattr(mod, "_wmic", fake)

    assert mod.get_path("SN-X") == "D:"


# ── 私有 _common._wmic（间接覆盖） ───────────────────────────────────


def _patch_wmic_run(monkeypatch, common, stdout: str, returncode: int = 0):
    """把 _common 内 subprocess 换成返回固定 CSV 的假实现，返回记录的命令行。"""
    calls: list[str] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="boom")

    monkeypatch.setattr(common, "subprocess", SimpleNamespace(run=fake_run))
    return calls


def test_common_wmic_parses_csv_rows(monkeypatch):
    """wmic CSV 文本 → 丢弃首列 Node、首行当表头、跳过空行的字典列表。"""
    common = _mod(_COMMON)
    stdout = (
        "Node,MediaType,SerialNumber\n"
        "\n"
        "PC,SSD,SN-1\n"
        "PC,HDD,SN-2\n"
    )
    calls = _patch_wmic_run(monkeypatch, common, stdout)

    rows = common._wmic("diskdrive get MediaType,SerialNumber")

    assert rows == [
        {"MediaType": "SSD", "SerialNumber": "SN-1"},
        {"MediaType": "HDD", "SerialNumber": "SN-2"},
    ]
    assert calls[0] == "wmic diskdrive get MediaType,SerialNumber /FORMAT:CSV"


@pytest.mark.parametrize("stdout", ["", "Node\n", "\n\n"])
def test_common_wmic_returns_empty_when_insufficient_rows(monkeypatch, stdout):
    """只有表头或无内容 → []。"""
    common = _mod(_COMMON)
    _patch_wmic_run(monkeypatch, common, stdout)

    assert common._wmic("diskdrive get Index") == []


def test_common_wmic_raises_on_failure(monkeypatch):
    """wmic 非零退出 → RuntimeError（消息含 stderr）。"""
    common = _mod(_COMMON)
    _patch_wmic_run(monkeypatch, common, "", returncode=1)

    with pytest.raises(RuntimeError, match="wmic 失败"):
        common._wmic("diskdrive get Index")
