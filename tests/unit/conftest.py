# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单元测试公共夹具。"""

import pytest

from tests.unit import _support


@pytest.fixture
def fake_device_repo():
    """返回一个空的内存 Device 仓储替身。"""
    return _support.FakeDeviceRepository()


@pytest.fixture
def fake_volume_repo():
    """返回一个空的内存 Volume 仓储替身。"""
    return _support.FakeVolumeRepository()


@pytest.fixture
def fake_super_device_repo():
    """返回一个空的内存 SuperDevice 仓储替身。"""
    return _support.FakeSuperDeviceRepository()


@pytest.fixture
def fake_super_volume_repo():
    """返回一个空的内存 SuperVolume 仓储替身。"""
    return _support.FakeSuperVolumeRepository()


@pytest.fixture
def fake_file_repo():
    """返回一个空的内存 File 仓储替身。"""
    return _support.FakeFileRepository()


@pytest.fixture
def fake_hasher():
    """返回可注入 file_service 的假哈希器。"""
    return _support.FakeHasher()


@pytest.fixture
def fake_file_service():
    """返回记录型假 file_service（不落库、不计算哈希）。"""
    return _support.FakeFileService()


@pytest.fixture
def fake_system_functions(monkeypatch):
    """在 volume service 模块内替换所有系统探测函数为桩。"""
    import application.storage.volume.service as mod

    calls = {}

    def stub(name, value):
        def fn(*args, **kwargs):
            calls.setdefault(name, []).append((args, kwargs))
            return value

        monkeypatch.setattr(mod, name, fn)

    stub("is_mount_point", True)
    stub("is_volume", False)
    stub("get_super_device_id", "SUPER-1")
    stub("get_volume_capacity", 2_000_000_000_000)
    stub("get_file_system", "ntfs")
    stub("get_volume_serial_by_path", None)
    stub("get_path", "/mnt/vol")
    return calls
