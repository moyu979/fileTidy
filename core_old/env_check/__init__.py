"""
环境检查模块
用于检查系统依赖和环境配置
"""

from .checker import check_dependencies
from .linux.dependencies import check_linux_dependencies

__all__ = ["check_dependencies", "check_linux_dependencies"]
