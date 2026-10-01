# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/linux/get_path.py（含 _common._lsblk）。

目的（测什么）：
    1. get_path 调 ``lsblk -J`` 取 JSON，展平 ``children`` 后按 serial 匹配并
       返回 mountpoint；命令失败、无匹配、mountpoint 为 null 时返回 None；
    2. 私有 ``_common._lsblk`` 的设备查找规则（按挂载点或 ``/dev/<name>``
       匹配，递归展平 children）与 ``_disk_info`` 找不到时抛 RuntimeError
       （不单独建测试文件，断言并入本文件）。

输入：
    - 打桩 ``mod.subprocess`` 的假 lsblk JSON 输出；
    - 打桩 ``_common.subprocess`` 的假 lsblk JSON 输出。

期望输出：
    - 挂载点字符串或 None；_lsblk 返回设备字典或 None。
"""

from __future__ import annotations

import importlib
import json
from types import SimpleNamespace

import pytest

_TARGET = "infra.system.storage.device.linux.get_path"
_COMMON = "infra.system.storage.device.linux._common"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _patch_subprocess(monkeypatch, mod, stdout: str, returncode: int = 0):
    """把模块内 subprocess 换成返回固定 stdout 的假实现。"""
    monkeypatch.setattr(
        mod, "subprocess",
        SimpleNamespace(run=lambda *a, **k: SimpleNamespace(
            returncode=returncode, stdout=stdout, stderr="boom",
        )),
    )


def _tree() -> str:
    """构造含嵌套 children 的 lsblk JSON 文本。"""
    return json.dumps({
        "blockdevices": [
            {
                "name": "sda", "serial": "X1", "mountpoint": None,
                "children": [],
            },
            {
                "name": "sdb", "serial": None, "mountpoint": None,
                "children": [
                    {"name": "sdb1", "serial": "TARGET", "mountpoint": "/mnt/data"},
                ],
            },
        ]
    })


# ── get_path ─────────────────────────────────────────────────────────


def test_get_path_matches_nested_child_serial(monkeypatch):
    """序列号在嵌套子设备上 → 返回该子设备的挂载点。"""
    mod = _mod(_TARGET)
    _patch_subprocess(monkeypatch, mod, _tree())

    assert mod.get_path("TARGET") == "/mnt/data"


def test_get_path_returns_none_when_serial_absent(monkeypatch):
    """没有任何设备序列号匹配 → None。"""
    mod = _mod(_TARGET)
    _patch_subprocess(monkeypatch, mod, _tree())

    assert mod.get_path("NO-SUCH-SERIAL") is None


def test_get_path_returns_none_when_mountpoint_is_null(monkeypatch):
    """序列号匹配但未挂载（mountpoint 为 null）→ None。"""
    mod = _mod(_TARGET)
    _patch_subprocess(
        monkeypatch, mod,
        json.dumps({"blockdevices": [{"name": "sda", "serial": "TARGET", "mountpoint": None}]}),
    )

    assert mod.get_path("TARGET") is None


def test_get_path_returns_none_when_lsblk_fails(monkeypatch):
    """lsblk 非零退出 → None（不抛异常）。"""
    mod = _mod(_TARGET)
    _patch_subprocess(monkeypatch, mod, "", returncode=1)

    assert mod.get_path("TARGET") is None


# ── 私有 _common 辅助（间接覆盖） ────────────────────────────────────


def test_common_lsblk_matches_by_mountpoint(monkeypatch):
    """入参是挂载点 → 返回对应设备字典。"""
    common = _mod(_COMMON)
    _patch_subprocess(
        monkeypatch, common,
        json.dumps({"blockdevices": [{"name": "sda", "mountpoint": "/mnt/data"}]}),
    )

    dev = common._lsblk("/mnt/data")

    assert dev is not None
    assert dev["name"] == "sda"


def test_common_lsblk_matches_by_device_path_in_nested_child(monkeypatch):
    """入参是 /dev/<name> 且位于 children 中 → 递归展平后命中。"""
    common = _mod(_COMMON)
    _patch_subprocess(
        monkeypatch, common,
        json.dumps({
            "blockdevices": [
                {"name": "sdb", "mountpoint": None,
                 "children": [{"name": "sdb1", "mountpoint": "/mnt/data"}]},
            ]
        }),
    )

    dev = common._lsblk("/dev/sdb1")

    assert dev is not None
    assert dev["name"] == "sdb1"


def test_common_lsblk_returns_none_and_disk_info_raises(monkeypatch):
    """无匹配 → _lsblk 返回 None；_disk_info 则抛 RuntimeError。"""
    common = _mod(_COMMON)
    _patch_subprocess(monkeypatch, common, json.dumps({"blockdevices": []}))

    assert common._lsblk("/dev/nope") is None
    with pytest.raises(RuntimeError, match="无法通过 lsblk 找到设备"):
        common._disk_info("/dev/nope")


def test_common_lsblk_raises_on_command_failure(monkeypatch):
    """lsblk 非零退出 → _lsblk 抛 RuntimeError。"""
    common = _mod(_COMMON)
    _patch_subprocess(monkeypatch, common, "", returncode=1)

    with pytest.raises(RuntimeError, match="lsblk 失败"):
        common._lsblk("/dev/sda")
