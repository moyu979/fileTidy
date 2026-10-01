# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/device/darwin/get_path.py（含 _common._disk_info）。

目的（测什么）：
    1. get_path 调 ``diskutil list`` 扫描 ``/dev/diskN``，逐个查 info 匹配
       Serial Number，命中则返回 Mount Point；命令失败、匹配不到、
       Mount Point 为空、单盘查询抛 RuntimeError 时分别返回 None 或继续；
    2. 私有 ``_common._disk_info`` 对 ``diskutil info`` 输出的 "key: value"
       解析规则与失败时抛 RuntimeError（不单独建测试文件，断言并入本文件）。

输入：
    - 打桩 ``mod.subprocess`` 的假 ``diskutil list`` 输出；
    - 打桩 ``mod._disk_info`` 的假 info 字典；
    - 打桩 ``_common.subprocess`` 的假 ``diskutil info`` 输出。

期望输出：
    - 匹配到的挂载点字符串；无匹配时 None；命令非零退出时报错或 None。
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

_TARGET = "infra.system.storage.device.darwin.get_path"
_COMMON = "infra.system.storage.device.darwin._common"


def _mod(dotted: str):
    """按点分路径导入真实模块对象（绕开包 __init__ 的同名属性覆盖）。"""
    return importlib.import_module(dotted)


def _fake_subprocess(stdout: str, returncode: int = 0, stderr: str = ""):
    """构造只提供 run 的假 subprocess 模块。"""
    return SimpleNamespace(
        run=lambda *a, **k: SimpleNamespace(
            returncode=returncode, stdout=stdout, stderr=stderr,
        ),
    )


# ── get_path ─────────────────────────────────────────────────────────


def test_get_path_matches_serial_and_returns_mount_point(monkeypatch):
    """diskutil list 扫描出的磁盘中匹配序列号 → 返回其挂载点。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(
        mod, "subprocess",
        _fake_subprocess("/dev/disk0\n/dev/disk1\n/dev/disk2s1\n"),
    )
    infos = {
        "/dev/disk0": {"Serial Number": "OTHER"},
        "/dev/disk1": {"Serial Number": "TARGET", "Mount Point": "/Volumes/Data"},
    }
    monkeypatch.setattr(mod, "_disk_info", lambda path: infos[path])

    assert mod.get_path("TARGET") == "/Volumes/Data"


def test_get_path_runtime_error_on_one_disk_is_skipped(monkeypatch):
    """某个磁盘查询抛 RuntimeError → 跳过继续扫描下一个。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "subprocess", _fake_subprocess("/dev/disk0\n/dev/disk1\n"))

    def fake_info(path: str) -> dict[str, str]:
        if path == "/dev/disk0":
            raise RuntimeError("diskutil info 失败")
        return {"Serial Number": "TARGET", "Mount Point": "/Volumes/Skip"}

    monkeypatch.setattr(mod, "_disk_info", fake_info)

    assert mod.get_path("TARGET") == "/Volumes/Skip"


def test_get_path_returns_none_when_not_found(monkeypatch):
    """没有任何磁盘序列号匹配 → None。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "subprocess", _fake_subprocess("/dev/disk0\n"))
    monkeypatch.setattr(mod, "_disk_info", lambda path: {"Serial Number": "OTHER"})

    assert mod.get_path("TARGET") is None


def test_get_path_returns_none_when_mount_point_empty(monkeypatch):
    """序列号匹配但 Mount Point 为空 → None。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(mod, "subprocess", _fake_subprocess("/dev/disk0\n"))
    monkeypatch.setattr(
        mod, "_disk_info",
        lambda path: {"Serial Number": "TARGET", "Mount Point": ""},
    )

    assert mod.get_path("TARGET") is None


def test_get_path_returns_none_when_diskutil_list_fails(monkeypatch):
    """diskutil list 非零退出 → None，且不再调用 _disk_info。"""
    mod = _mod(_TARGET)
    monkeypatch.setattr(
        mod, "subprocess", _fake_subprocess("", returncode=1, stderr="boom"),
    )

    def boom(path):  # pragma: no cover - 不应被调用
        raise AssertionError("命令失败时不应查询磁盘信息")

    monkeypatch.setattr(mod, "_disk_info", boom)

    assert mod.get_path("TARGET") is None


# ── 私有 _common._disk_info 解析（间接覆盖） ─────────────────────────


def test_common_disk_info_parses_key_value_lines(monkeypatch):
    """diskutil info 多行文本 → 按首个冒号切分的 key/value 字典，无冒号行被忽略。"""
    common = _mod(_COMMON)
    stdout = (
        "   Device Identifier:         disk0\n"
        "   Disk Size:                 500.1 GB (500107862016 Bytes)\n"
        "   Volume Name:               My: Disk\n"
        "   NoColonLine\n"
        "\n"
    )
    monkeypatch.setattr(common, "subprocess", _fake_subprocess(stdout))

    info = common._disk_info("/dev/disk0")

    assert info["Device Identifier"] == "disk0"
    assert info["Disk Size"] == "500.1 GB (500107862016 Bytes)"
    assert info["Volume Name"] == "My: Disk"
    assert "NoColonLine" not in info


def test_common_disk_info_raises_on_failure(monkeypatch):
    """diskutil info 非零退出 → RuntimeError，消息含 stderr。"""
    common = _mod(_COMMON)
    monkeypatch.setattr(
        common, "subprocess",
        _fake_subprocess("", returncode=1, stderr="Could not find disk"),
    )

    with pytest.raises(RuntimeError, match="Could not find disk"):
        common._disk_info("/dev/nope")
