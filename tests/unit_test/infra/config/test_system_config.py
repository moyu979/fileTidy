# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/config/system_config —— 系统实时配置。

目的：验证 SystemConfig 注册表查询语义、内存信息的单次采样，
以及 summary() 的输出结构。

输入：mock psutil.virtual_memory / Process。
期望输出：data 全量键、内存键来自假数据、缺失键语义符合文档。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from infra.config import system_config as sysconf_mod
from infra.config.system_config import SystemConfig


@pytest.fixture
def fake_memory(monkeypatch):
    vm = SimpleNamespace(total=16_000_000_000, used=4_000_000_000,
                         available=12_000_000_000, percent=25.0)
    proc = SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=123_456))
    monkeypatch.setattr(sysconf_mod.psutil, "virtual_memory", lambda: vm)
    monkeypatch.setattr(sysconf_mod.psutil, "Process", lambda *a, **k: proc)
    return vm


def test_registered_keys_and_reads(fake_memory):
    """注册表含 14 个键；get/[]/contains/get_required 语义正确。"""
    cfg = SystemConfig()
    assert len(cfg._methods) == 14
    assert cfg.get("hostname")
    assert cfg.get("no_such_key", "dft") == "dft"
    assert cfg["mem_total"] == 16_000_000_000
    assert cfg["process_rss"] == 123_456
    assert "cpu_count" in cfg
    with pytest.raises(KeyError):
        cfg["missing"]
    with pytest.raises(KeyError):
        cfg.get_required("missing")


def test_data_snapshot_uses_fake_memory(fake_memory):
    """data → 内存键为假数据，其余键存在。"""
    cfg = SystemConfig()
    data = cfg.data
    assert data["mem_total"] == 16_000_000_000
    assert data["mem_used"] == 4_000_000_000
    assert data["mem_available"] == 12_000_000_000
    assert data["mem_percent"] == 25.0
    assert data["process_rss"] == 123_456
    assert data["platform"] in {"darwin", "linux", "win32"}


def test_reload_is_noop(fake_memory):
    """实时取数 → reload 恒 False。"""
    assert SystemConfig().reload() is False


def test_summary_structure(fake_memory):
    """summary → 文档定义的键集合。"""
    data = SystemConfig().summary()
    assert set(data) == {
        "hostname", "platform", "platform_info", "python_version",
        "cpu_count", "is_64bit", "pid", "cwd", "process",
        "mem_total", "mem_used", "mem_available", "mem_percent", "process_rss",
    }
    assert data["process_rss"] == 123_456
