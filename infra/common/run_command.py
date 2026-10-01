"""
命令执行模块

提供跨平台同步执行系统命令的功能，支持超时控制和错误处理。

主要功能：
    - 跨平台同步执行系统命令（Linux、Windows、macOS）
    - 返回命令的返回码、标准输出和标准错误
    - 支持超时控制（默认10秒，超时后终止整棵进程树）
    - 自动处理编码问题（优先使用UTF-8，回退到系统默认编码）

平台支持：
    - Linux: 支持所有标准命令
    - Windows: 支持 cmd.exe 和 PowerShell 命令
    - macOS: 支持所有标准 Unix 命令

使用示例：
    >>> from infra.common.run_command import run_command
    >>> # Linux/macOS 示例
    >>> code, stdout, stderr = run_command(["ls", "-l"])
    >>> # 字符串示例（经 shell 解释，可使用管道/重定向）
    >>> code, stdout, stderr = run_command("ls -l | head -5")
    >>> # Windows 示例
    >>> code, stdout, stderr = run_command(["powershell", "-Command", "Get-Process"])
    >>> if code == 0:
    >>>     print(stdout)
    >>> else:
    >>>     print(f"错误: {stderr}")

注意事项：
    - 列表格式（推荐）不经过 shell；字符串格式会交给 shell 解释执行
      （POSIX 为 /bin/sh -c，Windows 为 cmd.exe /c），因此禁止把外部输入
      拼进字符串命令，否则存在命令注入风险
    - 空字符串 cmd（""）会被 shell 当作空命令，静默返回 (0, "", "")，不报错
    - 如果命令执行超时，会抛出 subprocess.TimeoutExpired 异常，并尽力终止整棵
      进程树（POSIX 杀整个进程组、Windows 用 taskkill /T），因此 "cmd1 | cmd2"
      这类管道命令不会在后台继续跑下去；异常对象的 stdout/stderr 携带已读到的
      输出，块缓冲的子进程可能尚未 flush，此时为空
    - 命令的 stdin 与调用方隔离（指向 /dev/null）：读 stdin 的命令会立刻
      拿到 EOF，既不会抢走调用方的输入、也不会阻塞；代价是无法主动喂输入
    - 命令不存在、不可执行等系统异常原样上抛，不做包装：
      调用方可直接读取异常的 errno / strerror / filename
    - 输出按「UTF-8 → 系统默认编码 → 标准输出编码」顺序尝试解码，
      全部失败时用 errors="replace" 兜底，不会因乱码抛异常
    - 跨平台命令差异需要由调用者处理（如 Windows 用 dir，Linux/macOS 用 ls）
"""

import locale
import os
import signal
import subprocess
import sys
from typing import List, Tuple, Union

# 超时终止后回收输出与进程状态的兜底等待时间（秒）
_REAP_TIMEOUT = 5


def _candidate_encodings() -> List[str]:
    """按优先级列出候选解码编码：UTF-8 → 系统默认编码 → 标准输出编码。"""
    names = ["utf-8", locale.getpreferredencoding(False)]
    stdout_encoding = getattr(sys.stdout, "encoding", None)
    if stdout_encoding:
        names.append(stdout_encoding)

    candidates: List[str] = []
    for name in names:
        if name and name.lower() not in [seen.lower() for seen in candidates]:
            candidates.append(name)
    return candidates


def _decode_output(raw: bytes) -> str:
    """按候选编码依次尝试解码；全部失败时用 UTF-8 + replace 兜底。"""
    for encoding in _candidate_encodings():
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def _terminate_process_tree(process: "subprocess.Popen") -> None:
    """终止命令及其所有子进程（超时清理用，尽量整棵进程树）。

    Args:
        process: 待终止的 Popen 对象。
    """
    if sys.platform == "win32":
        # Windows 没有进程组信号，借 taskkill 连同子进程一起终止
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            return
        except OSError:
            process.kill()
            return

    # POSIX：start_new_session 令子进程自身即为组长，于是可以整组终止
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except OSError:
        process.kill()


def run_command(cmd: Union[List[str], str], timeout: float = 10) -> Tuple[int, str, str]:
    """
    同步运行一个命令，并返回输出结果
    
    Args:
        cmd: 要执行的命令
             - 列表格式（推荐）: ["ls", "-l", "/path"]，直接执行、不经过 shell
             - 字符串格式: "ls -l /path"，经 shell 解释执行，
               禁止拼接外部输入，否则存在命令注入风险；
               此形式下命令缺失由 shell 返回 127，不抛 FileNotFoundError
        timeout: 命令超时时间（秒，可为小数），默认 10 秒；
                 传 0 或负数表示「立即超时」，而非不限时
        
    Returns:
        Tuple[int, str, str]: (返回码, 标准输出, 标准错误)
            - 返回码: 0 表示成功，非0 表示失败；负数表示被信号 N 杀死
              （如 -9 即 SIGKILL），取相反数可得信号编号
            - 标准输出: 命令的标准输出内容（字符串）
            - 标准错误: 命令的错误输出内容（字符串）
            
    Raises:
        subprocess.TimeoutExpired: 命令执行超时
        FileNotFoundError: 列表形式下命令不存在时抛出
        TypeError: cmd 既不是字符串也不是命令序列（如传入 int、None）时抛出
        PermissionError: 命令存在但不可执行（目录、缺少执行位等）时由系统抛出
        IndexError: cmd 传入空列表时由 subprocess 抛出（本函数不做参数校验）

        以上异常均由 subprocess 原样上抛、不做包装，
        errno / strerror / filename 等属性完整保留。
        
    示例:
        >>> code, out, err = run_command(["echo", "hello"])
        >>> print(f"返回码: {code}, 输出: {out}")
    """
    popen_kwargs = {
        "stdin": subprocess.DEVNULL,  # 不继承调用方 stdin：命令拿到 EOF，不抢输入也不阻塞
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": isinstance(cmd, str),  # 仅字符串形式交给 shell 解释
    }
    if sys.platform != "win32":
        # 让命令另立 session/进程组，超时时可整棵进程树一起终止
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(cmd, **popen_kwargs)
    try:
        stdout_raw, stderr_raw = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_tree(process)
        try:
            stdout_raw, stderr_raw = process.communicate(timeout=_REAP_TIMEOUT)
        except subprocess.TimeoutExpired:
            stdout_raw, stderr_raw = exc.stdout, exc.stderr
        # 让异常携带清理后读到的输出，而不是超时瞬间的那一份
        exc.stdout, exc.stderr = stdout_raw, stderr_raw
        raise

    return (
        process.returncode,
        _decode_output(stdout_raw),
        _decode_output(stderr_raw),
    )
