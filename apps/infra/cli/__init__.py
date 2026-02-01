"""
CLI 命令行工具模块

提供网络 API 失效时的临时工具组，支持通过命令行管理设备、卷、文件等。
"""

from .cli import FileTidyCLI

__all__ = ['FileTidyCLI']
