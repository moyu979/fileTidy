from __future__ import annotations

import enum


class FileState(enum.Enum):
    UNKNOWN = "unknown"     # 刚登记，尚未校验真实性（如 CSV 导入）
    ONLINE = "online"       # 正常可用
    MISSING = "missing"     # 文件在磁盘上不存在
    DAMAGED = "damaged"     # 文件损坏（哈希校验失败）
    REMOVED = "removed"     # 已移除（软删除，记录仍保留在数据库中）
