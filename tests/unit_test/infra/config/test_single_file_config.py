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

import gc
import os
import weakref

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


class _Subscriber:
    """持有 received 列表的订阅者，用于验证弱引用自动失效。"""

    def __init__(self):
        self.received = []

    def handle(self, changed_keys):
        self.received.append(changed_keys)


class _SlottedSubscriber:
    """用 __slots__ 且未声明 __weakref__ → 实例不可被弱引用。"""

    __slots__ = ("received",)

    def __init__(self):
        self.received = []

    def handle(self, changed_keys):
        self.received.append(changed_keys)


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
    subscriber = _Subscriber()
    cfg.subscribe(subscriber.handle)

    _write(cfg_file, {"a": 1, "b": 3, "c": 4})
    _bump_mtime(cfg_file)
    cfg.reload()
    assert subscriber.received == [["b", "c"]]


def test_subscribe_rejects_non_method(tmp_path, fake_watcher):
    """订阅 lambda / 普通函数 → TypeError（无所有者对象，弱引用会立即失效）。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1})
    cfg = SingleFileConfig(cfg_file, fake_watcher)

    with pytest.raises(TypeError, match="对象方法"):
        cfg.subscribe(lambda keys: None)

    def plain_function(keys):
        pass

    with pytest.raises(TypeError, match="对象方法"):
        cfg.subscribe(plain_function)


def test_subscribe_rejects_builtin_method(tmp_path, fake_watcher):
    """C 内置方法（list.append）→ TypeError：WeakMethod 只认 Python 方法。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1})
    cfg = SingleFileConfig(cfg_file, fake_watcher)
    received = []

    with pytest.raises(TypeError, match="对象方法"):
        cfg.subscribe(received.append)


def test_subscribe_rejects_non_weakrefable_owner(tmp_path, fake_watcher):
    """所有者不可弱引用（__slots__ 未声明 __weakref__）→ TypeError。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1})
    cfg = SingleFileConfig(cfg_file, fake_watcher)

    with pytest.raises(TypeError, match="对象方法"):
        cfg.subscribe(_SlottedSubscriber().handle)


def test_subscriber_release_auto_unsubscribes(tmp_path, fake_watcher):
    """订阅者被释放 → 不阻止回收，且回调自动失效不再触发。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1})
    cfg = SingleFileConfig(cfg_file, fake_watcher)

    subscriber = _Subscriber()
    cfg.subscribe(subscriber.handle)
    observer = weakref.ref(subscriber)

    _write(cfg_file, {"a": 2})
    _bump_mtime(cfg_file)
    cfg.reload()
    assert subscriber.received == [["a"]]

    del subscriber
    gc.collect()
    assert observer() is None, "config 持有回调，阻止了订阅者被回收"

    # 订阅者已释放：后续变更不应报错，也不再有回调被触发
    _write(cfg_file, {"a": 3})
    _bump_mtime(cfg_file)
    assert cfg.reload() is True


def test_unsubscribe_stops_callback(tmp_path, fake_watcher):
    """unsubscribe 后不再触发；按 (所有者, 方法名) 匹配，重新求值也能命中。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1})
    cfg = SingleFileConfig(cfg_file, fake_watcher)
    subscriber = _Subscriber()
    cfg.subscribe(subscriber.handle)

    _write(cfg_file, {"a": 2})
    _bump_mtime(cfg_file)
    cfg.reload()
    assert subscriber.received == [["a"]]

    cfg.unsubscribe(subscriber.handle)    # 新的 bound method 对象，应能匹配

    _write(cfg_file, {"a": 3})
    _bump_mtime(cfg_file)
    cfg.reload()
    assert subscriber.received == [["a"]]


def test_unsubscribe_is_idempotent(tmp_path, fake_watcher):
    """重复 unsubscribe / 未订阅时 unsubscribe → 不报错、无副作用。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1})
    cfg = SingleFileConfig(cfg_file, fake_watcher)
    subscriber = _Subscriber()
    cfg.subscribe(subscriber.handle)

    cfg.unsubscribe(subscriber.handle)
    cfg.unsubscribe(subscriber.handle)
    cfg.unsubscribe(subscriber.handle)

    _write(cfg_file, {"a": 2})
    _bump_mtime(cfg_file)
    cfg.reload()
    assert subscriber.received == []


def test_subscriber_survives_when_held(tmp_path, fake_watcher):
    """外部仍持有订阅者引用时，回调照常触发（弱引用不误杀）。"""
    cfg_file = tmp_path / "base.yaml"
    _write(cfg_file, {"a": 1})
    cfg = SingleFileConfig(cfg_file, fake_watcher)
    subscriber = _Subscriber()
    cfg.subscribe(subscriber.handle)

    gc.collect()
    _write(cfg_file, {"a": 2})
    _bump_mtime(cfg_file)
    cfg.reload()
    assert subscriber.received == [["a"]]


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
