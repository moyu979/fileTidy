# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/runtime —— 运行时 OS 状态与平台分发。

目的（测什么）：验证 `set_os` / `current_os` / `resolve_platform` /
`current_platform` / `reset` / `init_sys_infra` 对显式 OS 的读写、未知 OS 回退到
`unknown` 平台包、平台模块缓存的复用与失效。

输入：`set_os` 平台名、`resolve_platform` 显式参数、伪造的 AppConfig 对象。

期望输出：`current_os` 返回显式值或回退 `sys.platform`；未知 OS 解析为 `unknown`；
`current_platform` 返回对应平台包模块并缓存；`reset` / `set_os` / `init_sys_infra` 清空缓存。
"""

from __future__ import annotations

import sys

import pytest

import infra.system.runtime as runtime


@pytest.fixture(autouse=True)
def _restore_runtime():
    """用例前后保存/恢复 `runtime._os` 并清空平台模块缓存。"""
    original_os = runtime._os
    runtime.reset()
    yield
    runtime._os = original_os
    runtime.reset()


class _FakeConf:
    """记录 `get` 调用参数、固定返回值的假 AppConfig。"""

    def __init__(self, value):
        self._value = value
        self.calls: list[tuple] = []

    def get(self, *keys):
        self.calls.append(keys)
        return self._value


def test_set_os_updates_current_os():
    """输入 set_os('linux') → current_os() 返回 'linux'。"""
    runtime.set_os("linux")
    assert runtime.current_os() == "linux"


def test_current_os_falls_back_to_sys_platform():
    """输入 _os 为 None（未显式设置） → current_os() 回退 sys.platform。"""
    runtime._os = None
    assert runtime.current_os() == sys.platform


def test_resolve_platform_defaults_to_current_os():
    """输入 set_os('win32') 后调用 resolve_platform() → 'win32'。"""
    runtime.set_os("win32")
    assert runtime.resolve_platform() == "win32"


def test_resolve_platform_explicit_argument_does_not_change_state():
    """输入 resolve_platform('darwin') → 返回 'darwin'，但 current_os() 不变。"""
    runtime.set_os("linux")
    assert runtime.resolve_platform("darwin") == "darwin"
    assert runtime.current_os() == "linux"


def test_resolve_platform_unknown_os_falls_back():
    """输入未知 OS 名 'solaris' → resolve_platform 回退 'unknown'。"""
    assert runtime.resolve_platform("solaris") == "unknown"
    assert runtime.resolve_platform("haiku") == "unknown"


def test_resolve_platform_empty_string_uses_current_os():
    """输入 空字符串（falsy） → 视为未提供，回退到 current_os() 的解析结果。"""
    runtime.set_os("linux")
    assert runtime.resolve_platform("") == "linux"
    runtime.set_os("solaris")
    assert runtime.resolve_platform("") == "unknown"


def test_unknown_os_loads_unknown_package():
    """输入 set_os('solaris') + current_platform('device') → unknown 平台包。"""
    runtime.set_os("solaris")
    module = runtime.current_platform("device")
    assert module.__name__ == "infra.system.storage.device.unknown"


def test_current_platform_loads_and_caches_per_os():
    """输入 同一 OS 连续两次 current_platform → 返回同一模块对象且写入缓存。"""
    runtime.set_os("darwin")
    first = runtime.current_platform("device")
    second = runtime.current_platform("device")
    assert first is second
    assert first.__name__ == "infra.system.storage.device.darwin"
    assert runtime._platform_modules == {"device.darwin": first}


def test_switching_os_returns_different_module():
    """输入 set_os('darwin') 与 set_os('linux') → 两次得到不同平台模块。"""
    runtime.set_os("darwin")
    darwin_mod = runtime.current_platform("device")
    runtime.set_os("linux")
    linux_mod = runtime.current_platform("device")
    assert darwin_mod is not linux_mod
    assert linux_mod.__name__ == "infra.system.storage.device.linux"


def test_set_os_clears_platform_cache():
    """输入 加载过平台模块后再 set_os → 缓存被清空。"""
    runtime.set_os("linux")
    runtime.current_platform("device")
    assert runtime._platform_modules
    runtime.set_os("win32")
    assert runtime._platform_modules == {}


def test_reset_clears_cache_but_still_resolves_module():
    """输入 reset() → 缓存清空，再次 current_platform 仍能拿到同一模块对象。"""
    runtime.set_os("darwin")
    loaded = runtime.current_platform("device")
    runtime.reset()
    assert runtime._platform_modules == {}
    assert runtime.current_platform("device") is loaded


def test_init_sys_infra_reads_config_and_clears_cache():
    """输入 假 AppConfig（platform=linux） → _os 更新且平台缓存被清空。"""
    runtime.set_os("darwin")
    runtime.current_platform("device")
    conf = _FakeConf("linux")
    runtime.init_sys_infra(conf)
    assert conf.calls == [("system", "platform", "unknown")]
    assert runtime.current_os() == "linux"
    assert runtime._platform_modules == {}


def test_init_sys_infra_unknown_value_falls_back():
    """输入 假 AppConfig（platform='freebsd'） → 解析回退 unknown 平台包。"""
    runtime.init_sys_infra(_FakeConf("freebsd"))
    assert runtime.current_os() == "freebsd"
    assert runtime.resolve_platform() == "unknown"
    assert runtime.current_platform("device").__name__ == (
        "infra.system.storage.device.unknown"
    )
