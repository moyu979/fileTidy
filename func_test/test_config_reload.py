"""功能测试：配置目录的真实加载与热重载。

目的：用临时 settings 目录构造真实 AppConfig，验证占位符替换、
reload 触发条件与“坏 YAML 保留旧值”行为。

输入：写入/修改 YAML 文件。
期望输出：配置值变化、reload 返回值与失败保护符合文档。
"""

from __future__ import annotations

import os

import yaml

from infra.config.app_config import AppConfig


def _write(settings: str, filename: str, data):
    path = settings / filename
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _bump(path):
    st = path.stat()
    os.utime(path, (st.st_atime, st.st_mtime + 1))


def test_real_app_config_reload_and_placeholder(tmp_path):
    """改 base.yaml → reload True 且新值生效；坏 YAML → 旧值保留。"""
    settings = tmp_path / "settings"
    settings.mkdir()
    _write(settings, "base.yaml", {"interval": 60, "ws": "${workspace_path}/x"})
    _write(settings, "database.yaml", {"path": "${workspace_path}/db.sqlite"})

    cfg = AppConfig(settings, workspace_path="/data/ws")
    try:
        assert cfg["base"]["ws"] == "/data/ws/x"
        assert cfg["database"]["path"] == "/data/ws/db.sqlite"

        base_path = settings / "base.yaml"
        _write(settings, "base.yaml", {"interval": 30, "extra": 1})
        _bump(base_path)
        assert cfg.reload("base") is True
        assert cfg["base"]["interval"] == 30
        assert cfg["base"]["extra"] == 1

        # reload 无变化 → False
        assert cfg.reload("base") is False

        # 坏 YAML → reload False，旧值保留
        base_path.write_text("{broken: [", encoding="utf-8")
        _bump(base_path)
        assert cfg.reload("base") is False
        assert cfg["base"]["interval"] == 30
    finally:
        cfg.stop_auto_reload()
        cfg.watcher.stop()
