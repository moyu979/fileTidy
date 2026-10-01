# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/path_manager/is_path —— 路径识别。

目的：验证 darwin/linux/win32 三套路径规则的判断结果，以及 is_path 按
sys.platform 分发。

输入：各类路径字符串（绝对路径、UNC、相对路径、纯字符串）。
期望输出：符合对应平台规则的 True/False。
"""

from __future__ import annotations

import sys

import pytest

from infra.system.path_manager.is_path import (
    _is_path_darwin,
    _is_path_linux,
    _is_path_windows,
    is_path,
)


@pytest.mark.parametrize("helper", [_is_path_darwin, _is_path_linux])
def test_unix_paths(helper):
    """Unix 规则：绝对/家目录/相对/含斜杠为路径。"""
    assert helper("/etc/hosts") is True
    assert helper("~/file") is True
    assert helper("./rel") is True
    assert helper("../rel") is True
    assert helper("a/b") is True
    assert helper("") is False
    assert helper("plain-name") is False


@pytest.mark.parametrize("helper", [_is_path_darwin, _is_path_linux])
def test_unix_existing_path(tmp_path, helper):
    """已存在的目录/文件即使无路径特征也算路径。"""
    assert helper(str(tmp_path)) is True


def test_windows_paths():
    """Windows 规则：盘符/UNC/反斜杠为路径。"""
    assert _is_path_windows("C:\\Windows") is True
    assert _is_path_windows("c:/windows") is True
    assert _is_path_windows("\\\\server\\share") is True
    assert _is_path_windows(".\\x") is True
    assert _is_path_windows("..\\x") is True
    assert _is_path_windows("a\\b") is True
    assert _is_path_windows("") is False
    assert _is_path_windows("plain") is False


def test_dispatch_follows_sys_platform(tmp_path, monkeypatch):
    """is_path 按 sys.platform 选择规则。"""
    assert is_path(str(tmp_path)) is True
    monkeypatch.setattr(sys, "platform", "linux")
    assert is_path("/etc") is True
    assert is_path("plain") is False
