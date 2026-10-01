# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：application/storage/volume/service —— VolumeService 编排。

目的：验证手动登记、设备归属校验、字段/info 更新、卷初始化（目录整理 +
文件登记调用）、CSV 纯数据登记。仓储用替身，系统探测/事件/ID 全部打桩。

输入：卷字段 / 临时目录 / DataFrame。
期望输出：JSON、仓储与目录结构、文件服务调用记录符合文档。
"""

from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import pytest

import application.storage.volume.service as service_mod
from application.storage.volume.service import VolumeService
from domain.storage.super_device.base import SuperDevice
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.events import (
    VolumeFieldUpdated,
    VolumeInfoChanged,
    VolumeRegistered,
)


@pytest.fixture
def service(fake_volume_repo, fake_device_repo, fake_super_device_repo,
            fake_file_service, monkeypatch):
    events = []
    monkeypatch.setattr(service_mod, "log_event", events.append)
    monkeypatch.setattr(service_mod, "generate_id", lambda suffix="": "VOL-GEN")
    fake_device_repo.reg_device(
        __import__("domain.storage.device", fromlist=["Device"]).Device.create(
            serial="D1",
        )
    )
    fake_super_device_repo.reg_super_device(
        SuperDevice.create(serial="SUPER-1", sdtype="single", devices=["D1"])
    )
    return (
        VolumeService(
            volume_repository=fake_volume_repo,
            file_svc=fake_file_service,
            device_repository=fake_device_repo,
            super_device_repository=fake_super_device_repo,
        ),
        fake_volume_repo,
        events,
        fake_file_service,
    )


def test_register_by_info_success(service):
    """全手动登记 → JSON、落库、VolumeRegistered。"""
    svc, repo, events, _ = service
    result = svc.register_volume_by_info(
        serial="V1",
        device_id="D1",
        name="我的卷",
        file_system="ntfs",
        capacity=123,
        unique_mount_point="/mnt/v",
        info={"note": "x"},
        volume_path="/mnt/v",
    )
    data = json.loads(result)
    assert data["serial"] == "V1"
    assert data["device_id"] == "D1"
    vol = repo.get_volume("V1")
    assert vol.name == "我的卷"
    assert vol.state == VolumeState.UNKNOWN
    assert json.loads(vol.info) == {"note": "x"}
    assert isinstance(events[-1], VolumeRegistered)


def test_register_by_info_duplicate_raises(service):
    """serial 已存在 → ValueError。"""
    svc, _, _, _ = service
    svc.register_volume_by_info(serial="V1", device_id="D1",
                                volume_path="/x", file_system="ntfs")
    with pytest.raises(ValueError, match="已存在"):
        svc.register_volume_by_info(serial="V1", device_id="D1",
                                    volume_path="/x", file_system="ntfs")


def test_resolve_device_id(service):
    """device/super_device 存在 → 通过；都不存在 → ValueError。"""
    svc, _, _, _ = service
    assert svc._resolve_device_id("D1", datetime.now()) == "D1"
    assert svc._resolve_device_id("SUPER-1", datetime.now()) == "SUPER-1"
    with pytest.raises(ValueError, match="无法解析"):
        svc._resolve_device_id("NOPE", datetime.now())


def test_normalize_info(service):
    """dict→JSON 串；字符串原样；空 → ''。"""
    svc, _, _, _ = service
    assert svc._normalize_info({"a": 1}) == json.dumps({"a": 1}, ensure_ascii=False)
    assert svc._normalize_info('{"a":1}') == '{"a":1}'
    assert svc._normalize_info(None) == ""
    assert svc._normalize_info("") == ""


def test_setters(service):
    """set_name/device_id/state/capacity → (旧,新) + 事件。"""
    svc, repo, events, _ = service
    svc.register_volume_by_info(serial="V1", device_id="D1",
                                volume_path="/x", file_system="ntfs")
    old, new = svc.set_name("V1", "renamed")
    assert (old, new) == ("V1", "renamed")
    assert isinstance(events[-1], VolumeFieldUpdated)

    old, new = svc.set_device_id("V1", "SUPER-1")
    assert new == "SUPER-1"
    assert repo.get_volume("V1").device_id == "SUPER-1"

    old, new = svc.set_state("V1", VolumeState.FAULT)
    assert old == VolumeState.UNKNOWN and new == VolumeState.FAULT

    old, new = svc.set_capacity("V1", 55)
    assert (old, new) == (None, 55)


def test_set_device_id_invalid_target(service):
    """新归属不是已登记设备 → ValueError。"""
    svc, _, _, _ = service
    svc.register_volume_by_info(serial="V1", device_id="D1",
                                volume_path="/x", file_system="ntfs")
    with pytest.raises(ValueError):
        svc.set_device_id("V1", "GHOST")


def test_info_ops(service):
    """info 三操作 → replace/add/remove。"""
    svc, _, events, _ = service
    svc.register_volume_by_info(serial="V1", device_id="D1",
                                volume_path="/x", file_system="ntfs")
    svc.set_info("V1", {"k": 1})
    svc.append_info("V1", {"k": 2, "j": 3})
    svc.delete_info("V1", "k")
    ops = [e.op for e in events if isinstance(e, VolumeInfoChanged)]
    assert ops == ["replace", "add", "remove"]


def test_init_volume_organizes_directory(service, tmp_path, fake_system_functions):
    """init_volume：挂载点内容收进 datas、meta 写入 serial、登记卷与文件目录。"""
    svc, repo, events, file_svc = service
    mount = tmp_path / "mount"
    mount.mkdir()
    (mount / "a.txt").write_text("hello", encoding="utf-8")

    volume = svc.init_volume(
        path=str(mount),
        name="卷名",
        unique_mount_point="/mnt/ump",
        info={"x": 1},
    )

    assert volume.serial == "VOL-GEN"
    assert volume.file_system == "ntfs"          # 来自系统桩
    assert (mount / "datas" / "a.txt").is_file()
    assert (mount / "meta" / "VOL-GEN").is_file()
    assert not (mount / "a.txt").exists()
    assert repo.is_exist("VOL-GEN")
    assert file_svc.register_folder_calls[-1]["volume_serial"] == "VOL-GEN"
    assert isinstance(events[-1], VolumeRegistered)


def test_register_volume_by_csv_data(service):
    """纯数据 CSV 登记 → 卷落库且 file_service.register_by_csv 被调用。"""
    svc, repo, events, file_svc = service
    df = pd.DataFrame([
        {"sha512": "s1", "hash": "m1", "size": 10, "path": "/mnt/v/datas/a.txt"},
    ])
    result = svc.register_volume_by_csv_data(
        df=df,
        serial="CSV-VOL",
        device_id="D1",
        file_system="exfat",
        capacity=100,
        volume_path="/mnt/v",
        add_time=datetime(2026, 1, 1),
    )
    assert json.loads(result)["serial"] == "CSV-VOL"
    assert repo.is_exist("CSV-VOL")
    assert file_svc.register_by_csv_calls[-1]["volume_serial"] == "CSV-VOL"
    assert events[-1].__class__.__name__ == "VolumeRegistered"


def test_reg_volume_duplicate_serial_raises(service, tmp_path, monkeypatch):
    """登记已有卷时 serial 已落库 → ValueError（与 register_volume_by_info 一致）。"""
    svc, repo, events, _ = service
    monkeypatch.setattr(service_mod, "is_mount_point", lambda path: True)
    monkeypatch.setattr(service_mod, "is_volume", lambda path: True)
    monkeypatch.setattr(service_mod, "get_super_device_id", lambda path: "SUPER-1")
    monkeypatch.setattr(service_mod, "get_volume_capacity", lambda path: 100)
    monkeypatch.setattr(service_mod, "get_file_system", lambda path: "ntfs")

    mount = tmp_path / "vol"
    (mount / "datas").mkdir(parents=True)
    (mount / "meta").mkdir()
    (mount / "meta" / "V1").touch()

    svc.reg_volume(str(mount), register_files=False)
    assert repo.is_exist("V1")

    with pytest.raises(ValueError, match="已存在"):
        svc.reg_volume(str(mount), register_files=False)

    registered = [e for e in events if e.__class__.__name__ == "VolumeRegistered"]
    assert len(registered) == 1
