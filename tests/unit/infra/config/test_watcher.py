# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/config/watcher —— ConfigWatcher 分发与去抖。

目的：验证 register/unregister 的路径注册表、同路径覆盖、
以及 _handle 按 0.3 秒去抖调用 reload 回调。

输入：注册路径、模拟时钟。
期望输出：注册路径命中且去抖，未注册路径忽略。
"""

from __future__ import annotations

from infra.config.watcher import ConfigWatcher


def test_initial_state_is_not_running(tmp_path):
    """新实例未 start → is_running False；stop 幂等无异常。"""
    watcher = ConfigWatcher(tmp_path)
    assert watcher.is_running is False
    watcher.stop()


def test_register_overwrite_and_unregister(tmp_path, monkeypatch):
    """同路径重复注册覆盖；unregister 移除。"""
    watcher = ConfigWatcher(tmp_path)
    monkeypatch.setattr(watcher, "start", lambda: None)
    path = tmp_path / "a.yaml"

    calls = []
    watcher.register(path, lambda: calls.append("old"))
    watcher.register(path, lambda: calls.append("new"))
    assert len(watcher._reload_map) == 1

    watcher.unregister(path)
    assert path.resolve() not in watcher._reload_map
    watcher._handle(str(path))
    assert calls == []


def test_handle_debounces_and_dispatches(tmp_path, monkeypatch):
    """_handle：首调执行、0.3s 内去抖、之后再次执行。"""
    watcher = ConfigWatcher(tmp_path)
    now = [100.0]
    monkeypatch.setattr("infra.config.watcher.time.time", lambda: now[0])

    target = tmp_path / "b.yaml"
    count = []
    watcher._reload_map[str(target.resolve())] = lambda: count.append(1)

    watcher._handle(str(target))
    watcher._handle(str(target))          # 去抖窗口内，被忽略
    assert len(count) == 1

    now[0] += 1.0                          # 越过 0.3s 去抖
    watcher._handle(str(target))
    assert len(count) == 2


def test_unregistered_path_is_ignored(tmp_path, monkeypatch):
    """_handle 未注册路径 → 不调用回调。"""
    watcher = ConfigWatcher(tmp_path)
    count = []
    watcher._handle(str(tmp_path / "not-registered.yaml"))
    assert count == []
