# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/common/run_command —— 系统命令执行。

目的：验证 run_command 返回 (returncode, stdout, stderr) 三元组、
列表与字符串两种命令形式的差异、命令不存在/不可执行与超时的异常路径，
以及输出编码的自适应解码。

输入：命令列表或命令字符串、超时秒数、构造好的编码环境。
期望输出：按文档约定的返回值或异常；非 UTF-8 输出退化为可读字符串。
"""

from __future__ import annotations

import errno
import os
import subprocess
import sys
import time

import pytest

from infra.common import run_command as run_command_module
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


def test_missing_command_preserves_errno_and_filename():
    """命令不存在 → FileNotFoundError 原样上抛，errno/strerror/filename 均保留。

    输入：不存在的命令名。
    期望输出：errno 为 ENOENT，filename 为原始命令名（不做包装，属性不丢）。
    """
    missing = "definitely-not-a-real-cmd-xyz"

    with pytest.raises(FileNotFoundError) as excinfo:
        run_command([missing])

    error = excinfo.value
    assert error.errno == errno.ENOENT
    assert error.strerror == os.strerror(errno.ENOENT)
    assert error.filename == missing


def test_non_executable_path_raises_permission_error(tmp_path):
    """命令存在但缺少执行位 → PermissionError 原样上抛，且 errno 保留。

    输入：tmp_path 下一个无执行位的普通文件。
    期望输出：PermissionError，errno 为 EACCES（本函数不做包装，属性不丢）。
    """
    target = tmp_path / "not-executable.txt"
    target.write_text("data", encoding="utf-8")

    with pytest.raises(PermissionError) as excinfo:
        run_command([str(target)])

    assert excinfo.value.errno == errno.EACCES


def test_timeout_raises_timeout_expired():
    """sleep 2 且 timeout=0.2 → subprocess.TimeoutExpired。"""
    with pytest.raises(subprocess.TimeoutExpired):
        run_command(["sleep", "2"], timeout=0.2)


def test_string_command_runs_through_shell():
    """字符串命令 "echo hello" → 交给 shell 解释，返回 (0, 含 hello 的输出, "")。"""
    code, out, err = run_command("echo hello")

    assert code == 0
    assert out == "hello\n"
    assert err == ""


def test_string_command_interprets_shell_syntax():
    """字符串命令里的分号由 shell 解释 → 两条语句都执行。

    输入："echo first; echo second"；期望输出：两行都在 stdout。
    """
    code, out, _ = run_command("echo first; echo second")

    assert code == 0
    assert out.splitlines() == ["first", "second"]


def test_string_command_missing_command_returns_127():
    """字符串形式下命令不存在 → 由 shell 报 127 返回码，不抛异常。

    与列表形式不同：列表形式找不到可执行文件会抛 FileNotFoundError。
    """
    code, _, err = run_command("definitely-not-a-real-cmd-xyz")

    assert code == 127
    assert err != ""


def test_non_utf8_output_is_replaced_not_raised():
    """非 UTF-8 字节输出 → 返回可读字符串，不抛 UnicodeDecodeError。

    输入：sh -c "printf '\\377'" 产生单个 0xFF 字节。
    期望输出：returncode 0，stdout 为替换字符，类型为 str。
    """
    code, out, _ = run_command(["sh", "-c", "printf '\\377'"])

    assert code == 0
    assert isinstance(out, str)
    assert out == "\ufffd"


def test_decode_output_falls_back_to_system_encoding(monkeypatch):
    """UTF-8 解不开时回退到系统默认编码 → GBK 字节被正确还原为中文。

    输入："中文输出".encode("gbk")，并把系统默认编码置为 gbk。
    期望输出：解码结果与原文一致。
    """
    payload = "中文输出".encode("gbk")
    monkeypatch.setattr(
        run_command_module.locale, "getpreferredencoding", lambda *args: "gbk"
    )

    assert run_command_module._decode_output(payload) == "中文输出"


def test_decode_output_never_raises(monkeypatch):
    """候选编码全部解不开 → 用 replace 兜底，不抛异常。

    输入：既非 UTF-8 也非 GBK 的字节串。
    期望输出：仍返回 str，且其中的 ASCII 部分保留。
    """
    monkeypatch.setattr(
        run_command_module.locale, "getpreferredencoding", lambda *args: "gbk"
    )

    result = run_command_module._decode_output(b"\xff\xfe\x00\x01abc")

    assert isinstance(result, str)
    assert "abc" in result


def test_child_stdin_points_to_dev_null():
    """命令的 stdin 被隔离 → 子进程 fd 0 指向 /dev/null，而非调用方的输入。

    输入：让子进程打印自己 fd 0 的 (st_dev, st_ino)。
    期望输出：与 /dev/null 的 (st_dev, st_ino) 一致。
    """
    null_id = (os.stat(os.devnull).st_dev, os.stat(os.devnull).st_ino)

    _, out, _ = run_command(
        [sys.executable, "-c", "import os; s=os.fstat(0); print(s.st_dev, s.st_ino)"]
    )

    assert tuple(int(value) for value in out.split()) == null_id


def test_command_reading_stdin_gets_eof_instead_of_blocking():
    """读 stdin 的命令 → 立刻拿到 EOF，不阻塞也不抢调用方输入。

    输入：sh -c "read x; echo got=$x"，不提供任何输入。
    期望输出：read 立即因 EOF 失败，$x 为空，分号后的 echo 照常执行。
    """
    code, out, _ = run_command(["sh", "-c", "read x; echo got=$x"])

    assert code == 0
    assert out == "got=\n"


def _count_matching_processes(pattern: str) -> int:
    """统计命令行匹配 pattern 的进程数（pgrep 无结果时退出码为 1）。"""
    result = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True)
    return len(result.stdout.split())


def test_timeout_kills_pipeline_grandchildren():
    """管道命令超时 → 连同子进程一起终止，不在后台留下残留进程。

    输入：字符串命令 "sleep 137 | cat"，timeout 很短（不需要真跑完）。
    期望输出：抛 TimeoutExpired，且超时后 sleep 137 进程已不存在。
    """
    with pytest.raises(subprocess.TimeoutExpired):
        run_command("sleep 137 | cat", timeout=0.5)
    try:
        deadline = time.monotonic() + 3
        while _count_matching_processes("sleep 137") and time.monotonic() < deadline:
            time.sleep(0.05)
        assert _count_matching_processes("sleep 137") == 0
    finally:
        # 万一断言失败，别把 137 秒的 sleep 留在机器上
        subprocess.run(["pkill", "-f", "sleep 137"], capture_output=True)
