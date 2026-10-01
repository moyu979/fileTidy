# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/file/get_file_size —— 文件大小获取。

目的（测什么）：验证 `get_file_size(path)` 的分支行为：普通文件返回字节数、
目录与非法路径抛 ValueError、不存在路径抛 FileNotFoundError、底层
PermissionError / OSError 被重新包装并保留原始信息。

输入：`tmp_path` 下构造的真实文件/目录，以及对 `os.path` 与 `os.path.getsize`
的 monkeypatch。

期望输出：正确的字节数或对应的异常类型与消息。
"""

from __future__ import annotations

import pytest

import infra.system.storage.file.get_file_size as mod
from infra.system.storage.file.get_file_size import get_file_size


def test_regular_ascii_file_returns_byte_count(tmp_path):
    """输入 内容为 10 字节的普通文件 → 返回 10。"""
    target = tmp_path / "a.bin"
    target.write_bytes(b"0123456789")
    assert get_file_size(str(target)) == 10


def test_empty_file_returns_zero(tmp_path):
    """输入 空文件 → 返回 0。"""
    target = tmp_path / "empty.txt"
    target.write_text("", encoding="utf-8")
    assert get_file_size(str(target)) == 0


def test_multibyte_utf8_content_counts_bytes(tmp_path):
    """输入 内容为 '中文' 的 UTF-8 文件 → 返回 6（字节数而非字符数）。"""
    target = tmp_path / "cn.txt"
    target.write_text("中文", encoding="utf-8")
    assert get_file_size(str(target)) == 6


def test_missing_path_raises_file_not_found(tmp_path):
    """输入 不存在的路径 → 抛 FileNotFoundError 且消息含路径。"""
    missing = tmp_path / "nope.txt"
    with pytest.raises(FileNotFoundError) as excinfo:
        get_file_size(str(missing))
    assert str(missing) in str(excinfo.value)


def test_directory_raises_value_error(tmp_path):
    """输入 目录路径 → 抛 ValueError，消息标明是目录。"""
    with pytest.raises(ValueError, match="目录"):
        get_file_size(str(tmp_path))


def test_path_neither_file_nor_dir_raises_value_error(tmp_path, monkeypatch):
    """输入 存在但既非文件也非目录（打桩 isdir/isfile 为 False） → ValueError。"""
    monkeypatch.setattr(mod.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(mod.os.path, "isdir", lambda _p: False)
    monkeypatch.setattr(mod.os.path, "isfile", lambda _p: False)
    with pytest.raises(ValueError, match="既不是文件也不是目录"):
        get_file_size(str(tmp_path / "weird"))


def test_permission_error_is_rewrapped(tmp_path, monkeypatch):
    """输入 getsize 抛 PermissionError（打桩） → 重新包装为 PermissionError 且含路径。"""
    target = tmp_path / "locked.txt"
    target.write_text("x", encoding="utf-8")

    def _raise(_path):
        raise PermissionError("denied")

    monkeypatch.setattr(mod.os.path, "getsize", _raise)
    with pytest.raises(PermissionError) as excinfo:
        get_file_size(str(target))
    assert "没有权限访问文件" in str(excinfo.value)
    assert str(target) in str(excinfo.value)


def test_os_error_is_rewrapped(tmp_path, monkeypatch):
    """输入 getsize 抛 OSError（打桩） → 重新包装为 OSError 且保留原始信息。"""
    target = tmp_path / "broken.bin"
    target.write_bytes(b"data")

    def _raise(_path):
        raise OSError("io broken")

    monkeypatch.setattr(mod.os.path, "getsize", _raise)
    with pytest.raises(OSError) as excinfo:
        get_file_size(str(target))
    assert "获取文件大小失败" in str(excinfo.value)
    assert "io broken" in str(excinfo.value)
