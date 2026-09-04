# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/common/run_command —— 系统命令执行。

目的：验证 run_command 返回 (returncode, stdout, stderr) 三元组、
命令不存在时抛 FileNotFoundError、超时时抛 subprocess.TimeoutExpired。

输入：命令列表与超时秒数。
期望输出：按文档约定的返回值或异常。
"""

from __future__ import annotations

import subprocess

import pytest

from infra.common.run_command import run_command


def test_successful_command_returns_triple():
    """echo hello → (0, 含 hello 的 stdout, 空 stderr)。"""
    code, out, err = run_command(["echo", "hello"])
    assert code == 0
    assert "hello" in out
    assert err == ""


def test_failing_command_returns_nonzero():
    """sh -c 'exit 3' → returncode 3。"""
    code, _, _ = run_command(["sh", "-c", "exit 3"])
    assert code == 3


def test_missing_command_raises_file_not_found():
    """不存在的命令 → FileNotFoundError。"""
    with pytest.raises(FileNotFoundError):
        run_command(["definitely-not-a-real-cmd-xyz"])


def test_timeout_raises_timeout_expired():
    """sleep 2 且 timeout=0.2 → subprocess.TimeoutExpired。"""
    with pytest.raises(subprocess.TimeoutExpired):
        run_command(["sleep", "2"], timeout=0.2)
