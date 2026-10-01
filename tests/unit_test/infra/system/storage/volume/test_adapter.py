# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/volume/adapter —— 已废弃适配层占位模块。

目的（测什么）：`adapter.py` 是已废弃的兼容占位文件，只保留模块 docstring 以避免
既有 `import` 报错；验证它可被正常导入、docstring 明确标注「已废弃」，且模块内不含
任何公开符号（既没有 `SystemVolumeAdapter` 也没有函数/类）。

输入：通过 `importlib` 导入 `infra.system.storage.volume.adapter`。

期望输出：导入成功；`__doc__` 含「已废弃」；公开属性列表为空；不存在
`SystemVolumeAdapter` 属性。
"""

from __future__ import annotations

import importlib

MODULE_NAME = "infra.system.storage.volume.adapter"


def test_module_imports_without_error():
    """输入 模块名 → 导入成功并返回模块对象。"""
    module = importlib.import_module(MODULE_NAME)
    assert module.__name__ == MODULE_NAME


def test_docstring_marks_deprecated():
    """输入 模块 docstring → 包含「已废弃」说明，提示调用方可直接导入系统函数。"""
    module = importlib.import_module(MODULE_NAME)
    doc = module.__doc__ or ""
    assert "已废弃" in doc
    assert "系统函数可直接导入使用" in doc


def test_module_exposes_no_public_symbols():
    """输入 模块命名空间 → 除 dunder 外没有公开属性（无转发函数/类）。"""
    module = importlib.import_module(MODULE_NAME)
    public = [name for name in vars(module) if not name.startswith("__")]
    assert public == []


def test_no_legacy_adapter_symbol():
    """输入 模块属性查询 → 不存在已移除的 SystemVolumeAdapter。"""
    module = importlib.import_module(MODULE_NAME)
    assert not hasattr(module, "SystemVolumeAdapter")
