# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/volume —— 卷系统交互函数。

目的：锁定这些占位函数与用户的交互协议：文件系统菜单选择、容量整数输入、
空输入返回 None、y/n 判定。

输入：monkeypatch builtins.input 的应答序列。
期望输出：与应答对应的返回值。
"""

from __future__ import annotations

from infra.system.storage.volume.get_file_system import get_file_system
from infra.system.storage.volume.get_id import get_id
from infra.system.storage.volume.get_path import get_path
from infra.system.storage.volume.get_super_device_id import get_super_device_id
from infra.system.storage.volume.get_volume_capacity import get_volume_capacity
from infra.system.storage.volume.get_volume_serial_by_path import get_volume_serial_by_path
from infra.system.storage.volume.is_mount_point import is_mount_point


def test_get_file_system_menu_loop(monkeypatch, capsys):
    """先输非法编号再输 2 → exfat（菜单循环）。"""
    answers = iter(["9", "2"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert get_file_system("/mnt/x") == "exfat"
    assert "请选择卷类型" in capsys.readouterr().out


def test_get_file_system_direct_string(monkeypatch):
    """直接输入文件系统字符串 ntfs → ntfs。"""
    monkeypatch.setattr("builtins.input", lambda _: "ntfs")
    assert get_file_system("/mnt/x") == "ntfs"


def test_is_mount_point_yes_and_no(monkeypatch):
    """输入 y → True；输入 n → False。"""
    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert is_mount_point("/mnt/x") is True
    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert is_mount_point("/mnt/x") is False


def test_get_volume_capacity(monkeypatch):
    """输入整数 → int；空 → None。"""
    monkeypatch.setattr("builtins.input", lambda _: "12345")
    assert get_volume_capacity("/mnt/x") == 12345
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert get_volume_capacity("/mnt/x") is None


def test_get_path_and_id_empty(monkeypatch):
    """空输入 → None。"""
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert get_path("S-1") is None
    assert get_id("/mnt/x") is None


def test_get_super_device_id_returns_stripped(monkeypatch):
    """输入带空白的 super device id → strip 后返回。"""
    monkeypatch.setattr("builtins.input", lambda _: "  SD-1  ")
    assert get_super_device_id("/mnt/x") == "SD-1"


def test_get_volume_serial_by_path(monkeypatch):
    """输入 serial → 返回；空 → None。"""
    monkeypatch.setattr("builtins.input", lambda _: "V-7")
    assert get_volume_serial_by_path("/mnt/x") == "V-7"
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert get_volume_serial_by_path("/mnt/x") is None
