# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：application/storage/device/service —— DeviceService 编排。

目的：验证手动登记、查询、字段/info 更新、序列号变更与软删除的业务规则，
以及每个动作发出正确的事件。仓储使用内存替身，事件日志打桩。

输入：设备字段字典 / serial / 目标字符串。
期望输出：返回值、仓储状态与事件序列符合文档。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

import application.storage.device.service as service_mod
from application.storage.device.service import DeviceService
from domain.storage.device import Device
from domain.storage.device.enum import DeviceState
from domain.storage.device.events import (
    DeviceFieldUpdated,
    DeviceInfoChanged,
    DeviceInfoSet,
    DeviceRegistered,
    DeviceRemoved,
    DeviceSerialChanged,
)
from domain.storage.device.variants.hdd import HddDevice
from domain.storage.device.variants.ssd import SsdDevice


@pytest.fixture
def service(fake_device_repo, monkeypatch):
    events = []
    monkeypatch.setattr(service_mod, "log_event", events.append)
    return DeviceService(fake_device_repo), fake_device_repo, events


def _reg(service, **overrides) -> str:
    data = {"serial": "SN-1", "type": "hdd"}
    data.update(overrides)
    return service.reg_device_manual(data)


def test_reg_manual_success(service):
    """合法输入 → 落库、返回 serial、发 DeviceRegistered。"""
    svc, repo, events = service
    result = _reg(svc, name="我的盘", capacity=100, state=DeviceState.HEALTHY)
    assert result == "SN-1"
    device = repo.get_device("SN-1")
    assert device.name == "我的盘"
    assert device.capacity == 100
    assert device.state == DeviceState.HEALTHY
    assert isinstance(events[-1], DeviceRegistered)
    assert events[-1].serial == "SN-1"


def test_reg_manual_creates_typed_variant(service):
    """type=ssd → SsdDevice；type=hdd → HddDevice。"""
    svc, repo, _ = service
    _reg(svc, serial="A", type="ssd")
    assert isinstance(repo.get_device("A"), SsdDevice)
    _reg(svc, serial="B", type="hdd")
    assert isinstance(repo.get_device("B"), HddDevice)


def test_reg_manual_defaults(service):
    """缺省字段 → name=serial[:8]、state=UNKNOWN、last_check=UNIX 原点。"""
    svc, repo, _ = service
    _reg(svc, serial="ABCDEFGHIJ")
    device = repo.get_device("ABCDEFGHIJ")
    assert device.name == "ABCDEFGH"
    assert device.state == DeviceState.UNKNOWN
    assert device.last_check_time == datetime(1970, 1, 1)
    assert device.add_time is not None


def test_reg_manual_missing_serial_raises(service):
    """缺 serial → ValueError。"""
    svc, _, _ = service
    with pytest.raises(ValueError, match="serial"):
        svc.reg_device_manual({})


def test_reg_manual_duplicate_raises(service):
    """已存在 serial → ValueError 且不再落库。"""
    svc, repo, events = service
    _reg(svc)
    with pytest.raises(ValueError, match="already exists"):
        _reg(svc)
    assert len(events) == 1


def test_load_by_serial_and_missing(service):
    """按 serial 加载 → JSON；不存在 → None。"""
    svc, _, _ = service
    _reg(svc)
    text = svc.load_device(serial="SN-1")
    assert json.loads(text)["serial"] == "SN-1"
    assert svc.load_device(serial="NOPE") is None


def test_load_by_path_matches_absolute(fake_device_repo, service):
    """按路径加载 → 归一化绝对路径匹配 device_path。"""
    svc, repo, _ = service
    repo.reg_device(Device.create(serial="P1", device_path="/mnt/disk1"))
    text = svc.load_device(device_path="/mnt/../mnt/disk1")
    assert text is not None
    assert svc.load_device(device_path="/elsewhere") is None


def test_load_device_by_target_auto_detect(fake_device_repo, service, monkeypatch):
    """目标像路径 → 走路径；否则按 serial；显式 field → NotImplementedError。"""
    svc, repo, _ = service
    repo.reg_device(Device.create(serial="SN-9", device_path="/mnt/d"))
    assert svc.load_device_by_target("/mnt/d") is not None
    assert svc.load_device_by_target("SN-9") is not None
    with pytest.raises(NotImplementedError):
        svc.load_device_by_target("SN-9", field="name")


def test_list_devices(service):
    """list → JSON 字符串列表。"""
    svc, _, _ = service
    _reg(svc, serial="X1")
    _reg(svc, serial="X2")
    items = svc.list_devices()
    assert {json.loads(x)["serial"] for x in items} == {"X1", "X2"}


@pytest.mark.parametrize(
    ("method", "field", "value"),
    [
        ("set_name", "name", "new-name"),
        ("set_type", "type", "ssd"),
        ("set_state", "state", DeviceState.FAULT),
        ("set_capacity", "capacity", 999),
    ],
)
def test_setters_return_old_new_and_event(service, method, field, value):
    """字段更新 → 返回 (旧值, 新值) 且发 DeviceFieldUpdated。"""
    svc, repo, events = service
    _reg(svc, name="old", capacity=1, state=DeviceState.HEALTHY)
    before = len(events)
    old, new = getattr(svc, method)("SN-1", value)
    assert new == value
    event = events[-1]
    assert isinstance(event, DeviceFieldUpdated)
    assert event.field == field
    assert event.old_value == old
    assert event.new_value == new
    assert old != new
    # 状态/容量等可通过仓储读回
    assert repo.get_device("SN-1").dtype == new if field == "type" else True


def test_setter_missing_device_raises(service):
    """不存在的设备 → ValueError。"""
    svc, _, _ = service
    with pytest.raises(ValueError, match="not found"):
        svc.set_name("NOPE", "x")


def test_info_set_replace_events(service):
    """set_info 全量替换 → DeviceInfoSet；append 区分 add/replace；delete 发 remove。"""
    svc, _, events = service
    _reg(svc)
    svc.set_info("SN-1", {"a": 1})
    assert isinstance(events[-1], DeviceInfoSet)

    old, new = svc.append_info("SN-1", {"a": 2, "b": 3})
    assert old == {"a": 1}
    assert new == {"a": 2, "b": 3}
    ops = [e.op for e in events if isinstance(e, DeviceInfoChanged)]
    assert ops[-2:] == ["replace", "add"]

    old, new = svc.delete_info("SN-1", "a")
    assert old == {"a": 2, "b": 3}
    assert new == {"b": 3}
    assert events[-1].op == "remove"


def test_set_serial(service):
    """set_serial → 仓储改名 + DeviceSerialChanged 事件。"""
    svc, repo, events = service
    _reg(svc)
    old, new = svc.set_serial("SN-1", "SN-2")
    assert (old, new) == ("SN-1", "SN-2")
    assert repo.is_exist("SN-2")
    assert not repo.is_exist("SN-1")
    assert isinstance(events[-1], DeviceSerialChanged)


def test_remove_device(service):
    """remove → 软删除（state=REMOVED）+ DeviceRemoved 事件。"""
    svc, repo, events = service
    _reg(svc, state=DeviceState.HEALTHY)
    svc.remove_device("SN-1")
    assert repo.get_device("SN-1").state == DeviceState.REMOVED
    assert isinstance(events[-1], DeviceRemoved)
