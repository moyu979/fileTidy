# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device 平台解析（mock 系统命令）。

目的：用假 diskutil/lsblk/smartctl 输出验证 darwin 与 linux 各函数的
解析规则（容量、状态、类型、序列号、路径查找），不触真实命令。

注意：平台包 __init__ 会把同名函数覆盖为包属性，因此这里一律用
importlib.import_module 取真正的模块对象再打桩。

输入：各平台命令返回的假 stdout/字典。
期望输出：按文档规则解析出的值或异常。
"""

from __future__ import annotations

import importlib
import json
from types import SimpleNamespace

import pytest

from domain.storage.device.enum import DeviceState


def _mod(dotted: str):
    return importlib.import_module(dotted)


# ── darwin ────────────────────────────────────────────────────────


def test_darwin_get_capacity(monkeypatch):
    """Disk Size 括号内字节 → int。"""
    mod = _mod("infra.system.storage.device.darwin.get_capacity")
    monkeypatch.setattr(
        mod, "_disk_info",
        lambda path: {"Disk Size": "500.1 GB (500107862016 Bytes)"},
    )
    assert mod.get_capacity("/dev/disk0") == 500107862016


def test_darwin_get_capacity_missing_raises(monkeypatch):
    """缺少 Disk Size → ValueError。"""
    mod = _mod("infra.system.storage.device.darwin.get_capacity")
    monkeypatch.setattr(mod, "_disk_info", lambda path: {})
    with pytest.raises(ValueError):
        mod.get_capacity("/dev/disk0")


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("Verified", DeviceState.HEALTHY),
        ("Failing", DeviceState.FAULT),
        ("Not Supported", DeviceState.UNKNOWN),
        ("", DeviceState.UNKNOWN),
    ],
)
def test_darwin_get_healthy(monkeypatch, status, expected):
    """SMART Status 文本 → 对应 DeviceState。"""
    mod = _mod("infra.system.storage.device.darwin.get_healthy")
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"SMART Status": status})
    assert mod.get_healthy("/dev/disk0") == expected


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        ({"Removable Media": "Removable", "Solid State": "Yes"}, "tf_sd_card"),
        ({"Solid State": "Yes", "Removable Media": "No"}, "ssd"),
        ({"Solid State": "No", "Removable Media": "No"}, "hdd"),
    ],
)
def test_darwin_get_type(monkeypatch, info, expected):
    """Removable/Solid State 字段 → 设备类型。"""
    mod = _mod("infra.system.storage.device.darwin.get_type")
    monkeypatch.setattr(mod, "_disk_info", lambda path: info)
    assert mod.get_type("/dev/disk0") == expected


def test_darwin_get_serial(monkeypatch):
    """Serial Number 存在 → 返回；缺失 → None。"""
    mod = _mod("infra.system.storage.device.darwin.get_serial")
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"Serial Number": "AAA123"})
    assert mod.get_serial("/dev/disk0") == "AAA123"
    monkeypatch.setattr(mod, "_disk_info", lambda path: {})
    assert mod.get_serial("/dev/disk0") is None


def test_darwin_is_disk(monkeypatch):
    """_disk_info 成功 → True；RuntimeError → False。"""
    mod = _mod("infra.system.storage.device.darwin.is_disk")
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"Serial Number": "X"})
    assert mod.is_disk("/dev/disk0") is True

    def boom(path):
        raise RuntimeError("no")

    monkeypatch.setattr(mod, "_disk_info", boom)
    assert mod.is_disk("/dev/disk0") is False


def test_darwin_get_path_by_serial(monkeypatch):
    """diskutil list 扫描磁盘 → 匹配序列号返回挂载点。"""
    mod = _mod("infra.system.storage.device.darwin.get_path")
    ok = SimpleNamespace(returncode=0, stdout="/dev/disk0\n/dev/disk1\n", stderr="")
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=lambda *a, **k: ok))
    infos = {
        "/dev/disk0": {"Serial Number": "OTHER"},
        "/dev/disk1": {"Serial Number": "TARGET", "Mount Point": "/Volumes/Data"},
    }
    monkeypatch.setattr(mod, "_disk_info", lambda path: infos[path])
    assert mod.get_path("TARGET") == "/Volumes/Data"


# ── linux ─────────────────────────────────────────────────────────


def test_linux_get_capacity(monkeypatch):
    """lsblk SIZE 文本 → 字节（1024 进制）。"""
    mod = _mod("infra.system.storage.device.linux.get_capacity")
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"name": "sda", "size": "100G"})
    assert mod.get_capacity("/dev/sda") == 100 * 1024**3


def test_linux_get_type(monkeypatch):
    """ROTA/模型 → ssd/hdd/tf_sd_card。"""
    mod = _mod("infra.system.storage.device.linux.get_type")
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"rota": 0})
    assert mod.get_type("/dev/sda") == "ssd"
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"rota": 1})
    assert mod.get_type("/dev/sda") == "hdd"
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"rota": 1, "model": "flash drive"})
    assert mod.get_type("/dev/sda") == "tf_sd_card"


def test_linux_get_serial(monkeypatch):
    """serial 字段 → 返回。"""
    mod = _mod("infra.system.storage.device.linux.get_serial")
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"serial": "LINUX-SN"})
    assert mod.get_serial("/dev/sda") == "LINUX-SN"


def test_linux_get_healthy(monkeypatch):
    """smartctl 输出 → PASSED=HEALTHY / FAILED=FAULT / 其他 UNKNOWN。"""
    mod = _mod("infra.system.storage.device.linux.get_healthy")
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"name": "sda"})

    def result(stdout, returncode=0):
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(
        mod, "subprocess",
        SimpleNamespace(run=lambda *a, **k: result("SMART overall-health PASSED")),
    )
    assert mod.get_healthy("/dev/sda") == DeviceState.HEALTHY

    monkeypatch.setattr(
        mod, "subprocess",
        SimpleNamespace(run=lambda *a, **k: result("FAILED")),
    )
    assert mod.get_healthy("/dev/sda") == DeviceState.FAULT

    monkeypatch.setattr(
        mod, "subprocess",
        SimpleNamespace(run=lambda *a, **k: result("", returncode=1)),
    )
    assert mod.get_healthy("/dev/sda") == DeviceState.UNKNOWN


def test_linux_get_path_by_serial(monkeypatch):
    """lsblk JSON → 匹配序列号返回挂载点。"""
    mod = _mod("infra.system.storage.device.linux.get_path")
    payload = json.dumps({
        "blockdevices": [
            {"name": "sda", "serial": "X1", "mountpoint": None},
            {
                "name": "sdb", "serial": None, "mountpoint": None,
                "children": [{"name": "sdb1", "serial": "TARGET", "mountpoint": "/mnt/data"}],
            },
        ]
    })
    monkeypatch.setattr(
        mod, "subprocess",
        SimpleNamespace(run=lambda *a, **k: SimpleNamespace(
            returncode=0, stdout=payload, stderr="",
        )),
    )
    assert mod.get_path("TARGET") == "/mnt/data"


def test_linux_is_disk(monkeypatch):
    """_disk_info 成功 → True；RuntimeError → False。"""
    mod = _mod("infra.system.storage.device.linux.is_disk")
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"name": "sda"})
    assert mod.is_disk("/dev/sda") is True

    def boom(path):
        raise RuntimeError("no")

    monkeypatch.setattr(mod, "_disk_info", boom)
    assert mod.is_disk("/dev/sda") is False
