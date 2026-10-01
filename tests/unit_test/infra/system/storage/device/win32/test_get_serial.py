# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/win32/get_serial.py（含 _common._get_drive_by_path）。

目的（测什么）：
    1. get_serial 取 diskdrive 字典的 "SerialNumber" 并 strip：有值返回，
       空白串/键缺失/磁盘找不到时返回 None；
    2. 私有 ``_common._get_drive_by_path`` 的路径→物理盘解析：PowerShell 取
       不到盘符抛 RuntimeError；逐级 wmic 查询命中则返回磁盘字典，未命中
       返回 None（不单独建测试文件，断言并入本文件）。

输入：
    - 打桩 ``mod._get_drive_by_path`` 返回的 diskdrive 字典；
    - 打桩 ``_common.subprocess`` 的假 PowerShell 输出与 ``_common._wmic``。

期望输出：
    - 序列号字符串或 None；物理盘字典或 RuntimeError/None。
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

_TARGET = "infra.system.storage.device.win32.get_serial"
_COMMON = "infra.system.storage.device.win32._common"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


# ── get_serial ───────────────────────────────────────────────────────


def test_get_serial_strips_value(monkeypatch):
    """SerialNumber 有值 → strip 后返回。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(
        mod, "_get_drive_by_path",
        lambda path: {"SerialNumber": "  SN-1  "},
    )

    assert mod.get_serial("C:\\") == "SN-1"


@pytest.mark.parametrize(
    "drive",
    [
        None,
        {},
        {"SerialNumber": ""},
        {"SerialNumber": "   "},
    ],
)
def test_get_serial_returns_none(monkeypatch, drive):
    """磁盘找不到或序列号为空/空白 → None。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "_get_drive_by_path", lambda path: drive)

    assert mod.get_serial("C:\\") is None


# ── 私有 _common._get_drive_by_path（间接覆盖） ───────────────────────


def _patch_powershell(monkeypatch, common, stdout: str):
    """把 _common 内 subprocess 换成返回固定盘符的假实现。"""
    monkeypatch.setattr(
        common, "subprocess",
        SimpleNamespace(run=lambda *a, **k: SimpleNamespace(
            returncode=0, stdout=stdout, stderr="",
        )),
    )


def test_get_drive_by_path_raises_when_drive_letter_missing(monkeypatch):
    """PowerShell 取不到盘符（空输出）→ RuntimeError。"""
    common = _mod(_COMMON)
    _patch_powershell(monkeypatch, common, "   \n")

    with pytest.raises(RuntimeError, match="无法找到路径对应的卷"):
        common._get_drive_by_path("E:\\")


def test_get_drive_by_path_returns_matching_disk(monkeypatch):
    """盘符取到且逐级 wmic 查询有结果 → 返回该物理盘字典。"""
    common = _mod(_COMMON)
    _patch_powershell(monkeypatch, common, "C:\n")

    responses = [
        [{"Index": "1", "SerialNumber": "SN-1", "Size": "100"}],  # diskdrive
        [{"DeviceID": "\\\\?\\disk#1"}],                          # partition
        [{"Dependent": "C:"}],                                    # assoc
    ]
    calls: list[str] = []

    def fake_wmic(cmd: str):
        calls.append(cmd)
        return responses.pop(0)

    monkeypatch.setattr(common, "_wmic", fake_wmic)

    drive = common._get_drive_by_path("C:\\")

    assert drive is not None
    assert drive["SerialNumber"] == "SN-1"
    assert "DiskIndex=1" in calls[1]


def test_get_drive_by_path_returns_none_when_partition_lookup_empty(monkeypatch):
    """物理盘存在但没有分区结果 → 返回 None。"""
    common = _mod(_COMMON)
    _patch_powershell(monkeypatch, common, "C:\n")

    responses = [[{"Index": "1"}], []]

    monkeypatch.setattr(common, "_wmic", lambda cmd: responses.pop(0))

    assert common._get_drive_by_path("C:\\") is None
