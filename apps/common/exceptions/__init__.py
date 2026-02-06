"""
统一异常定义模块

定义项目中使用的所有自定义异常类
"""

from apps.common.exceptions.hash_conflict_error import HashConflictError

__all__ = [
    'HashConflictError',
]
