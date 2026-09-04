# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 File 枚举定义 - 文件相关常量
# NOTE: file 子系统未完成（设计未定稿），以下为探索/临时实现，勿作为稳定功能依赖；后续可能整体重写或删除。

from __future__ import annotations

import enum


class FileState(enum.Enum):
    """文件状态枚举。

    定义被管理文件可能处于的各种状态。
    """
    UNKNOWN = "unknown"     # 刚登记，尚未校验真实性（如 CSV 导入）
    ONLINE = "online"       # 正常可用
    MISSING = "missing"     # 文件在磁盘上不存在
    DAMAGED = "damaged"     # 文件损坏（哈希校验失败）
    REMOVED = "removed"     # 已移除（软删除，记录仍保留在数据库中）
