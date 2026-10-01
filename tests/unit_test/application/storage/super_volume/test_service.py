# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：application/storage/super_volume/service —— SuperVolumeService。

目的：验证超级卷登记（serial/name 自动生成、子卷存在性、类型分派）、
子卷增删、字段/info 更新与软删除。仓储为内存替身。

输入：svtype / volumes / 字段值。
期望输出：JSON 结果、仓储状态与事件类型符合文档。
"""

from __future__ import annotations

import json

import pytest

import application.storage.super_volume.service as service_mod
from application.storage.super_volume.service import SuperVolumeService
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.super_volume.events import (
    SuperVolumeFieldUpdated,
    SuperVolumeInfoChanged,
    SuperVolumeRegistered,
    VolumesAddedToSuperVolume,
    VolumesRemovedFromSuperVolume,
)
from domain.storage.super_volume.variants.copy import CopySuperVolume
from domain.storage.volume import Volume
from domain.storage.volume.enum import VolumeState


def _make_volume(serial: str) -> Volume:
    return Volume.create(
        serial=serial, device_id="D", name=serial,
        add_time=None, last_check_time=None,
        state=VolumeState.HEALTHY, capacity=1,
        unique_mount_point=None, file_system="ntfs",
        info=None, volume_path=None,
    )


@pytest.fixture
def service(fake_super_volume_repo, fake_volume_repo, monkeypatch):
    events = []
    monkeypatch.setattr(service_mod, "log_event", events.append)
    monkeypatch.setattr(service_mod, "generate_id", lambda suffix="": "SV-GEN")
    for serial in ("V1", "V2", "V3"):
        fake_volume_repo.reg_volume(_make_volume(serial))
    return (
        SuperVolumeService(fake_super_volume_repo, fake_volume_repo),
        fake_super_volume_repo,
        events,
    )


def test_reg_super_volume_success(service):
    """合法输入 → JSON、CopySuperVolume、事件。"""
    svc, repo, events = service
    result = svc.reg_super_volume(volumes=["V1", "V2"], svtype="copy")
    data = json.loads(result)
    assert data["serial"] == "SV-GEN"
    assert data["volumes"] == ["V1", "V2"]
    sv = repo.get_super_volume("SV-GEN")
    assert isinstance(sv, CopySuperVolume)
    assert isinstance(events[-1], SuperVolumeRegistered)


def test_reg_requires_svtype(service):
    """缺 svtype → ValueError。"""
    svc, _, _ = service
    with pytest.raises(ValueError, match="svtype"):
        svc.reg_super_volume(volumes=["V1"])


def test_reg_requires_volumes(service):
    """空 volumes → ValueError。"""
    svc, _, _ = service
    with pytest.raises(ValueError, match="至少"):
        svc.reg_super_volume(svtype="copy", volumes=[])


def test_reg_unknown_volume_raises(service):
    """子卷不存在 → ValueError。"""
    svc, _, _ = service
    with pytest.raises(ValueError, match="不存在"):
        svc.reg_super_volume(svtype="copy", volumes=["NOPE"])


def test_reg_duplicate_raises(service):
    """serial 已存在 → ValueError。"""
    svc, _, _ = service
    svc.reg_super_volume(serial="SV1", svtype="copy", volumes=["V1"])
    with pytest.raises(ValueError, match="已存在"):
        svc.reg_super_volume(serial="SV1", svtype="copy", volumes=["V2"])


def test_get_and_list(service):
    """get/list 返回 JSON。"""
    svc, _, _ = service
    svc.reg_super_volume(serial="SV1", svtype="copy", volumes=["V1"])
    assert json.loads(svc.get_super_volume("SV1"))["serial"] == "SV1"
    assert svc.get_super_volume("NOPE") is None
    assert len(svc.list_super_volumes()) == 1


def test_add_and_remove_volumes(service):
    """加卷/移除卷 → 状态更新与事件。"""
    svc, repo, events = service
    svc.reg_super_volume(serial="SV1", svtype="copy", volumes=["V1"])

    result = svc.add_volumes(super_volume_serial="SV1", volume_ids=["V2"])
    assert json.loads(result)["volumes"] == ["V1", "V2"]
    assert isinstance(events[-1], VolumesAddedToSuperVolume)

    result = svc.remove_volumes(super_volume_serial="SV1", volume_ids=["V1"])
    assert json.loads(result)["volumes"] == ["V2"]
    assert isinstance(events[-1], VolumesRemovedFromSuperVolume)


def test_add_volumes_validation(service):
    """空参数 / 超级卷不存在 / 子卷不存在 → ValueError。"""
    svc, _, _ = service
    svc.reg_super_volume(serial="SV1", svtype="copy", volumes=["V1"])
    with pytest.raises(ValueError):
        svc.add_volumes(super_volume_serial="", volume_ids=["V2"])
    with pytest.raises(ValueError, match="不存在"):
        svc.add_volumes(super_volume_serial="SVX", volume_ids=["V2"])
    with pytest.raises(ValueError, match="不存在"):
        svc.add_volumes(super_volume_serial="SV1", volume_ids=["VX"])


@pytest.mark.parametrize(
    ("method", "field", "value"),
    [
        ("set_name", "name", "new-name"),
        ("set_svtype", "svtype", "snapraid_raid5"),
        ("set_state", "state", SuperVolumeState.FAULT),
    ],
)
def test_setters(service, method, field, value):
    """字段更新 → (旧,新) + SuperVolumeFieldUpdated。"""
    svc, _, events = service
    svc.reg_super_volume(serial="SV1", svtype="copy", volumes=["V1"])
    old, new = getattr(svc, method)("SV1", value)
    assert new == value
    assert isinstance(events[-1], SuperVolumeFieldUpdated)
    assert events[-1].field == field
    assert events[-1].old_value == old


def test_info_ops(service):
    """info 三操作 → replace/add/remove 事件。"""
    svc, _, events = service
    svc.reg_super_volume(serial="SV1", svtype="copy", volumes=["V1"])
    svc.set_info("SV1", {"k": 1})
    svc.append_info("SV1", {"k": 2, "j": 3})
    svc.delete_info("SV1", "k")
    ops = [e.op for e in events if isinstance(e, SuperVolumeInfoChanged)]
    assert ops == ["replace", "add", "remove"]
