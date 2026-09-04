# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/config/app_config —— 配置容器。

目的：验证 AppConfig 按文件名扫描 YAML、透传占位符、内置 system section，
以及统一的 reload / stop_auto_reload 语义。

输入：临时 settings 目录中的多个 YAML。
期望输出：按 section 聚合的配置与文档一致的查询结果。
"""

from __future__ import annotations

import pytest
import yaml

from infra.config import app_config as app_config_mod
from infra.config.app_config import AppConfig


class _FakeWatcher:
    def __init__(self, settings_dir=None):
        self.unregistered = []
        self.stopped = 0
        self.settings_dir = settings_dir

    def register(self, path, reload_fn):
        pass

    def unregister(self, path):
        self.unregistered.append(str(path))

    def start(self):
        pass

    def stop(self, timeout=None):
        self.stopped += 1

    @property
    def is_running(self):
        return False


def _make_settings(tmp_path) -> dict:
    settings = tmp_path / "settings"
    settings.mkdir()
    (settings / "base.yaml").write_text(
        yaml.safe_dump({"workspace_path": "ignored", "interval": 60}),
        encoding="utf-8",
    )
    (settings / "database.yaml").write_text(
        "path: '${workspace_path}/database.db'\n",
        encoding="utf-8",
    )
    return settings


def test_sections_and_reads(tmp_path, monkeypatch):
    """两个 yaml + system → sections 齐全且查询语义正确。"""
    monkeypatch.setattr(app_config_mod, "ConfigWatcher", _FakeWatcher)
    settings = _make_settings(tmp_path)
    cfg = AppConfig(settings, workspace_path="/data/ws")

    assert set(cfg.keys()) == {"base", "database", "system"}
    assert cfg["database"]["path"] == "/data/ws/database.db"
    assert cfg.get("base", "interval") == 60
    assert cfg.get_required("base", "interval") == 60
    assert cfg.get("base", "missing", "d") == "d"
    assert "system" in cfg
    assert "hostname" in cfg["system"].data


def test_reload_all_returns_list(tmp_path, monkeypatch):
    """reload(None) → 每个 section 一个布尔结果。"""
    monkeypatch.setattr(app_config_mod, "ConfigWatcher", _FakeWatcher)
    cfg = AppConfig(_make_settings(tmp_path), workspace_path=tmp_path)
    results = cfg.reload()
    assert isinstance(results, list)
    assert len(results) == 3


def test_system_section_has_no_hot_reload(tmp_path, monkeypatch):
    """对 system 注册 on_change / reload → TypeError。"""
    monkeypatch.setattr(app_config_mod, "ConfigWatcher", _FakeWatcher)
    cfg = AppConfig(_make_settings(tmp_path), workspace_path=tmp_path)
    with pytest.raises(TypeError):
        cfg.on_change("system", lambda keys: None)
    assert cfg.reload("system") is False


def test_stop_auto_reload_all(tmp_path, monkeypatch):
    """stop_auto_reload() → 所有 YAML section 注销监听，无异常。"""
    monkeypatch.setattr(app_config_mod, "ConfigWatcher", _FakeWatcher)
    cfg = AppConfig(_make_settings(tmp_path), workspace_path=tmp_path)
    cfg.stop_auto_reload()
    assert not cfg.is_auto_reload_running
