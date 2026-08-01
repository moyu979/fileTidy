# CHECK: 待检查 - 共享工具 - 系统命令执行器

"""
命令执行模块

提供跨平台同步执行系统命令的功能，支持超时控制和错误处理。

主要功能：
    - 跨平台同步执行系统命令（Linux、Windows、macOS）
    - 返回命令的返回码、标准输出和标准错误
    - 支持超时控制（默认10秒）
    - 自动处理编码问题（优先使用UTF-8，回退到系统默认编码）

平台支持：
    - Linux: 支持所有标准命令
    - Windows: 支持 cmd.exe 和 PowerShell 命令
    - macOS: 支持所有标准 Unix 命令

使用示例：
    >>> from utils.runCommand import run_command
    >>> # Linux/macOS 示例
    >>> code, stdout, stderr = run_command(["ls", "-l"])
    >>> # Windows 示例
    >>> code, stdout, stderr = run_command(["powershell", "-Command", "Get-Process"])
    >>> if code == 0:
    >>>     print(stdout)
    >>> else:
    >>>     print(f"错误: {stderr}")

注意事项：
    - cmd 参数应该是列表格式，如 ["ls", "-l"]，而不是字符串
    - 如果命令执行超时，会抛出 subprocess.TimeoutExpired 异常
    - 跨平台命令差异需要由调用者处理（如 Windows 用 dir，Linux/macOS 用 ls）
"""

import subprocess
import sys
from typing import List, Tuple, Union


def run_command(cmd: Union[List[str], str], timeout: int = 10) -> Tuple[int, str, str]:
    """
    同步运行一个命令，并返回输出结果
    
    Args:
        cmd: 要执行的命令，可以是列表（推荐）或字符串
             - 列表格式: ["ls", "-l", "/path"]
             - 字符串格式: "ls -l /path"（需要 shell=True，不推荐）
        timeout: 命令超时时间（秒），默认10秒
        
    Returns:
        Tuple[int, str, str]: (返回码, 标准输出, 标准错误)
            - 返回码: 0 表示成功，非0 表示失败
            - 标准输出: 命令的标准输出内容（字符串）
            - 标准错误: 命令的错误输出内容（字符串）
            
    Raises:
        subprocess.TimeoutExpired: 命令执行超时
        FileNotFoundError: 命令不存在
        ValueError: 命令参数无效
        
    示例:
        >>> code, out, err = run_command(["echo", "hello"])
        >>> print(f"返回码: {code}, 输出: {out}")
    """
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False  # 不自动抛出异常，由调用者处理返回码
        )
        
        # 跨平台编码处理：优先使用UTF-8，回退到系统默认编码
        encoding = 'utf-8'
        if sys.platform == 'win32':
            # Windows 系统可能使用 GBK 或其他编码
            try:
                encoding = sys.stdout.encoding or 'utf-8'
            except AttributeError:
                encoding = 'utf-8'
        
        # 尝试解码，如果失败则使用 errors='replace' 保留可读性
        try:
            stdout = result.stdout.decode(encoding)
        except UnicodeDecodeError:
            stdout = result.stdout.decode(encoding, errors='replace')
        
        try:
            stderr = result.stderr.decode(encoding)
        except UnicodeDecodeError:
            stderr = result.stderr.decode(encoding, errors='replace')
        
        return (result.returncode, stdout, stderr)
    except subprocess.TimeoutExpired as e:
        # 超时异常，直接重新抛出
        raise
    except FileNotFoundError:
        raise FileNotFoundError(f"命令不存在: {cmd[0] if isinstance(cmd, list) else cmd}")
    except ValueError as e:
        raise ValueError(f"命令参数无效: {e}")
