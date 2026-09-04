# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：application/storage/super_device/service —— SuperDeviceService。

目的：验证超级设备登记（含 serial 自动生成与路径归一化）、查询、
字段/info 更新、子设备增删换与软删除的编排；事件全部打桩。

输入：data 字典 / serial / 设备路径。
期望输出：返回值、仓储状态与事件类型符合文档。
"""

from __future__ import annotations

import json

import pytest

import application.storage.super_device.service as service_mod
from application.storage.super_device.service import SuperDeviceService
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_device.events import (
    SuperDeviceDeviceChanged,
    SuperDeviceFieldUpdated,
    SuperDeviceInfoChanged,
    SuperDeviceRegistered,
    SuperDeviceRemoved,
)
from domain.storage.super_device.variants.raidz import RaidzSuperDevice


@pytest.fixture
def service(fake_super_device_repo, fake_device_repo, monkeypatch):
    events = []
    monkeypatch.setattr(service_mod, "log_event", events.append)
    monkeypatch.setattr(service_mod, "generate_id", lambda suffix="": "GEN-SERIAL")
    return (
        SuperDeviceService(fake_super_device_repo, fake_device_repo),
        fake_super_device_repo,
        events,
    )


def _reg(service, **overrides):
    data = {"sdtype": "raidz", "devices": ["D1", "D2"], "name": "RAID-0"}
    data.update(overrides)
    return service.reg_super_device_manual(data)


def test_reg_manual_success(service):
    """合法输入 → 落库、事件、返回 serial；默认值正确。"""
    svc, repo, events = service
    serial = _reg(svc)
    assert serial == "GEN-SERIAL"
    sd = repo.get_super_device(serial)
    assert isinstance(sd, RaidzSuperDevice)
    assert sd.devices == ["D1", "D2"]
    assert sd.state == SuperDeviceState.HEALTHY
    assert sd.need_all_devices_online is True
    assert sd.capacity == -1
    assert isinstance(events[-1], SuperDeviceRegistered)


def test_reg_manual_keeps_user_serial(service):
    """传 serial → 不自动生成。"""
    svc, repo, _ = service
    _reg(svc, serial="MY-SD")
    assert repo.is_exist("MY-SD")


def test_reg_manual_missing_sdtype_raises(service):
    """缺 sdtype → ValueError。"""
    svc, _, _ = service
    with pytest.raises(ValueError, match="sdtype"):
        svc.reg_super_device_manual({"serial": "S"})


def test_reg_manual_duplicate_raises(service):
    """重复 serial → ValueError。"""
    svc, _, events = service
    _reg(svc, serial="DUP")
    with pytest.raises(ValueError, match="already exists"):
        _reg(svc, serial="DUP")
    assert len(events) == 1


def test_reg_single_requires_exactly_one_device(service):
    """sdtype=single + 空 devices → AssertionError。"""
    svc, _, _ = service
    with pytest.raises(AssertionError):
        _reg(svc, sdtype="single", devices=[])


def test_reg_converts_paths_to_serials(service, monkeypatch):
    """devices 里是路径 → 调 get_serial 转成序列号。"""
    svc, repo, _ = service
    monkeypatch.setattr(service_mod, "is_path", lambda x: x.startswith("/"))
    monkeypatch.setattr(service_mod, "get_serial", lambda path: f"SERIAL:{path}")
    _reg(svc, devices=["/dev/disk1"])
    sd = repo.get_super_device("GEN-SERIAL")
    assert sd.devices == ["SERIAL:/dev/disk1"]


def test_load_and_list(service):
    """get 单条 / list 全部。"""
    svc, repo, _ = service
    _reg(svc)
    assert json.loads(svc.load_super_device("GEN-SERIAL"))["type"] == "raidz"
    assert svc.load_super_device("NOPE") is None
    assert len(svc.list_super_devices()) == 1


def test_load_by_path_resolves_serial(service, monkeypatch):
    """给路径 → 通过 get_serial 解析。"""
    svc, _, _ = service
    monkeypatch.setattr(service_mod, "get_serial", lambda path: "PATH-SD")
    _reg(svc, serial="PATH-SD")
    assert svc.load_super_device(super_device_path="/dev/disk0") is not None


@pytest.mark.parametrize(
    ("method", "field", "value"),
    [
        ("set_name", "name", "new-name"),
        ("set_sdtype", "sdtype", "single"),
        ("set_state", "state", SuperDeviceState.FAULT),
        ("set_capacity", "capacity", 42),
        ("set_need_all_devices_online", "need_all_devices_online", False),
    ],
)
def test_setters_and_events(service, method, field, value):
    """字段更新 → (旧,新) + SuperDeviceFieldUpdated。"""
    svc, repo, events = service
    _reg(svc, serial="SD1")
    old, new = getattr(svc, method)("SD1", value)
    assert new == value
    event = events[-1]
    assert isinstance(event, SuperDeviceFieldUpdated)
    assert event.field == field
    assert event.old_value == old


def test_info_ops(service):
    """info 三操作 → 相应事件 op。"""
    svc, _, events = service
    _reg(svc, serial="SD1")
    svc.set_info("SD1", {"k": 1})
    svc.append_info("SD1", {"k": 2, "j": 3})
    svc.delete_info("SD1", "k")
    ops = [e.op for e in events if isinstance(e, SuperDeviceInfoChanged)]
    assert ops == ["replace", "add", "remove"]


def test_add_replace_remove_device(service):
    """子设备增/换/删 → 事件 old/new 语义正确。"""
    svc, repo, events = service
    fake_device_repo = svc.device_repository
    from domain.storage.device import Device

    for serial in ("D1", "D2", "D3"):
        fake_device_repo.reg_device(Device.create(serial=serial))
    _reg(svc, serial="SD1", devices=["D1"])

    svc.add_device("SD1", "D2")
    assert repo.get_super_device("SD1").devices == ["D1", "D2"]
    assert events[-1].new == "D2" and events[-1].old is None

    svc.replace_device("SD1", "D1", "D3")
    assert repo.get_super_device("SD1").devices == ["D3", "D2"]
    assert events[-1].old == "D1" and events[-1].new == "D3"

    svc.remove_device("SD1", "D3")
    assert repo.get_super_device("SD1").devices == ["D2"]
    assert events[-1].old == "D3" and events[-1].new is None


def test_add_device_requires_registered_device(service):
    """device_repository 存在但设备未登记 → ValueError。"""
    svc, _, _ = service
    _reg(svc, serial="SD1")
    with pytest.raises(ValueError, match="不存在"):
        svc.add_device("SD1", "NOT-REGISTERED")


def test_remove_super_device(service):
    """remove → REMOVED + 事件。"""
    svc, repo, events = service
    _reg(svc, serial="SD1")
    svc.remove_super_device("SD1")
    assert repo.get_super_device("SD1").state == SuperDeviceState.REMOVED
    assert isinstance(events[-1], SuperDeviceRemoved)
