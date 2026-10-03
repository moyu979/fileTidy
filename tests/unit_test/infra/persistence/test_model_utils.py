# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/_model_utils.py —— 从 ORM 模型自动派生可更新字段。

目的（测什么）：
- `updatable_fields` 恰好等于「模型表列名 - 主键列」；
- 主键 serial 被排除（改名须走 update_serial，不得经通用 update 通道）；
- lru_cache 生效（重复调用返回同一对象），语义稳定。

输入：DeviceModel / SuperDeviceModel 两个真实模型类。

期望输出：字段集合与模型列定义一致，且不含主键。
"""

from __future__ import annotations

from infra.persistence._model_utils import updatable_fields
from infra.persistence.models import DeviceModel, SuperDeviceModel


def test_updatable_fields_excludes_primary_key():
    """输入 DeviceModel → 期望输出 含业务列、不含主键 serial。"""
    fields = updatable_fields(DeviceModel)
    assert "serial" not in fields
    assert {"name", "dtype", "state", "capacity", "info"} <= fields


def test_updatable_fields_matches_table_columns_minus_pk():
    """输入 真实模型类 → 期望输出 恰为表列名去掉主键列。"""
    for model in (DeviceModel, SuperDeviceModel):
        cols = {col.name for col in model.__table__.columns}
        pk = {col.name for col in model.__table__.primary_key.columns}
        assert updatable_fields(model) == frozenset(cols - pk)
        assert "serial" not in updatable_fields(model)


def test_updatable_fields_is_cached():
    """输入 重复调用 → 期望输出 返回同一缓存对象（lru_cache 生效且不改语义）。"""
    assert updatable_fields(SuperDeviceModel) is updatable_fields(SuperDeviceModel)
