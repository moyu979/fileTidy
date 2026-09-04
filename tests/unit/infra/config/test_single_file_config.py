# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/config/single_file_config —— 单文件配置热更。

目的：
- 验证 YAML 加载、${key} 占位符替换、下标/宽松/严格读取语义；
- 验证 reload 的 mtime 变更检测、失败保留旧配置、变更回调；
- 验证缺失文件 / 非法 YAML / 非映射根节点的 fail-fast 行为。

输入：临时 YAML 文本与替换表。
期望输出：按文档描述的配置数据或异常。
"""

from __future__ import annotations

import os

import pytest
import yaml

from infra.config.single_file_config import SingleFileConfig


class _FakeWatcher:
    """记录注册/注销调用、不启动任何线程的假监听器。"""

    def __init__(self):
        self.registered = []
        self.unregistered = []

    def register(self, path, reload_fn):
        self.registered.append((str(path), reload_fn))

    def unregister(self, path):
        self.unregistered.append(str(path))

    @property
    def is_running(self):
        return False


@pytest.fixture
def fake_watcher():
    return _FakeWatcher()


def _write(path, data: dict):
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _bump_mtime(path):
    st = path.stat()
    os.utime(path, (st.st_atime, st.st_mtime + 1))


def test_load_and_placeholder_replacement(tmp_path, fake_watcher):
    """${workspace_path} 占位符 → 替换为注入值。"""
    cfg_file = tmp_path / "base.yaml"
    cfg_file.write_text("path: '${workspace_path}/database.db'\n", encoding="utf-8")
    cfg = SingleFileConfig(
        cfg_file, fake_watcher, replacements={"workspace_path": "/data"}
    )
    assert cfg["path"] == "/data/database.db"


def test_read_semantics(tmp_path, fake_watcher):
    """配置数据支持 get/get_required/[]/contains/data。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1, "b": {"c": 2}})
    cfg = SingleFileConfig(cfg_file, fake_watcher)

    assert cfg.get("a") == 1
    assert cfg.get("missing", "dft") == "dft"
    assert cfg.get_required("a") == 1
    assert cfg["b"]["c"] == 2
    assert "a" in cfg
    assert "missing" not in cfg
    assert cfg.data == {"a": 1, "b": {"c": 2}}

    with pytest.raises(KeyError):
        cfg["missing"]
    with pytest.raises(KeyError):
        cfg.get_required("missing")


def test_constructor_registers_watcher(tmp_path, fake_watcher):
    """构造时注册 reload 回调到 watcher。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1})
    cfg = SingleFileConfig(cfg_file, fake_watcher)
    assert len(fake_watcher.registered) == 1
    assert fake_watcher.registered[0][0] == str(cfg_file)


def test_reload_only_on_change(tmp_path, fake_watcher):
    """文件未变 reload → False；内容变化 reload → True 并更新。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1, "b": 2})
    cfg = SingleFileConfig(cfg_file, fake_watcher)
    assert cfg.reload() is False

    _write(cfg_file, {"a": 1, "b": 3, "c": 4})
    _bump_mtime(cfg_file)
    assert cfg.reload() is True
    assert cfg.data == {"a": 1, "b": 3, "c": 4}


def test_change_callback_receives_changed_keys(tmp_path, fake_watcher):
    """内容变化 → 回调收到排序后的变更键。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1, "b": 2})
    cfg = SingleFileConfig(cfg_file, fake_watcher)
    received = []
    cfg.on_change(received.append)

    _write(cfg_file, {"a": 1, "b": 3, "c": 4})
    _bump_mtime(cfg_file)
    cfg.reload()
    assert received == [["b", "c"]]


def test_reload_keeps_old_data_on_bad_yaml(tmp_path, fake_watcher):
    """新内容解析失败 → reload False 且旧数据保留。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1})
    cfg = SingleFileConfig(cfg_file, fake_watcher)

    cfg_file.write_text("{invalid: [", encoding="utf-8")
    _bump_mtime(cfg_file)
    assert cfg.reload() is False
    assert cfg["a"] == 1


def test_stop_auto_reload_unregisters(tmp_path, fake_watcher):
    """stop_auto_reload → watcher.unregister 被调用。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1})
    cfg = SingleFileConfig(cfg_file, fake_watcher)
    cfg.stop_auto_reload()
    assert str(cfg_file) in fake_watcher.unregistered


def test_missing_file_raises(tmp_path, fake_watcher):
    """配置文件不存在 → FileNotFoundError。"""
    with pytest.raises(FileNotFoundError):
        SingleFileConfig(tmp_path / "nope.yaml", fake_watcher)


def test_non_mapping_root_raises(tmp_path, fake_watcher):
    """YAML 根节点是列表 → ValueError。"""
    cfg_file = tmp_path / "bad.yaml"
    cfg_file.write_text("- 1\n- 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="映射"):
        SingleFileConfig(cfg_file, fake_watcher)
