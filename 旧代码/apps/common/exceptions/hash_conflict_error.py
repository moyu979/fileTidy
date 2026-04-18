"""
哈希值冲突异常
"""


class HashConflictError(Exception):
    """哈希值冲突异常：路径已存在但哈希值不匹配"""
    pass
