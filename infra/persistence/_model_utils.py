"""infra/persistence 内部工具：从 ORM 模型自动派生可更新字段。

避免在 `update_device` / `update_super_device` 里硬编码字段白名单 —— 白名单直接
取自模型的表列定义，随模型漂移自动更新。主键列被排除：改主键必须走专用的
`update_serial` / `update_super_device_serial`（它们会同步迁移关联表引用，
通用 update 通道不会）。
"""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=None)
def updatable_fields(model_cls: type) -> frozenset[str]:
    """返回模型的「可经通用 update_* 修改」字段名集合。

    取模型表列名去掉主键列（如 ``DeviceModel.serial``）。序列号是主键，改名必须走
    ``update_serial`` / ``update_super_device_serial``（会迁移 volumes.device_id /
    super_device_structures.* 等引用），不允许从通用 update 通道修改。

    Args:
        model_cls: SQLAlchemy 声明式模型类。

    Returns:
        可更新字段名的 frozenset（如 ``{"name", "dtype", "state", ...}``）。
    """
    table = model_cls.__table__
    pk = {col.name for col in table.primary_key.columns}
    return frozenset(col.name for col in table.columns if col.name not in pk)
