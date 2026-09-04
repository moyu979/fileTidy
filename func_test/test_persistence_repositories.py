"""功能测试：五个仓储在真实 SQLite 上的持久化行为。

目的：
- Device / Volume / SuperDevice / SuperVolume / File 仓储的 CRUD；
- 外键/唯一约束与业务占用校验（DeviceInUseError / VolumeInUseError /
  SubDevice*Error / SuperDeviceInUseError）；
- 序列号迁移的级联更新。

输入：每个用例独立 sqlite 临时库与领域对象。
期望输出：数据库行、查询结果与异常类型符合各仓储 docstring。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from domain.storage.device.enum import DeviceState
from domain.storage.device.errors import DeviceInUseError
from domain.storage.file.enum import FileState
from domain.storage.file.new_file import NewFile
from domain.storage.super_device.enum import RelationState, SuperDeviceState
from domain.storage.super_device.errors import (
    SubDeviceInUseError,
    SubDeviceNotFoundError,
    SubDeviceUnavailableError,
    SuperDeviceInUseError,
)
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.errors import VolumeInUseError
from infra.persistence.models import (
    FileLocationsModel,
    FileSourcesModel,
    SuperDeviceStructureModel,
    SuperVolumeStructureModel,
    VolumeModel,
)

from func_test._helpers import make_device, make_super_device, make_super_volume, make_volume


# ── DeviceRepository ──────────────────────────────────────────────


def test_device_repository_crud(repos):
    """登记/查询/列出/更新设备 → 行为符合接口。"""
    repo = repos["device"]
    device = make_device("D1", dtype="ssd")

    repo.reg_device(device)
    assert repo.is_exist("D1") is True
    assert repo.is_exist(device) is True
    assert repo.is_exist("NOPE") is False

    got = repo.get_device("D1")
    assert got.serial == "D1"
    assert got.dtype == "ssd"
    assert got.state == DeviceState.HEALTHY
    assert [d.serial for d in repo.list_devices()] == ["D1"]

    repo.update_device("D1", name="new-name", state=DeviceState.DANGER)
    got = repo.get_device("D1")
    assert got.name == "new-name"
    assert got.state == DeviceState.DANGER

    with pytest.raises(ValueError):
        repo.update_device("NOPE", name="x")


def test_device_repository_update_serial_cascades(repos):
    """设备改名 → volumes.device_id 与 structures.sub_device_id 级联。"""
    device_repo = repos["device"]
    sd_repo = repos["super_device"]
    volume_repo = repos["volume"]

    device_repo.reg_device(make_device("D1"))
    device_repo.reg_device(make_device("D2"))
    sd_repo.reg_super_device(make_super_device("SD1", devices=["D1", "D2"]))
    volume_repo.reg_volume(make_volume("V1", device_id="D1"))

    device_repo.update_serial("D1", "D1-NEW")

    assert device_repo.is_exist("D1-NEW")
    assert not device_repo.is_exist("D1")
    assert volume_repo.get_volume("V1").device_id == "D1-NEW"
    assert sd_repo.get_super_device("SD1").devices == ["D1-NEW", "D2"]


def test_device_remove_blocked_by_super_device(repos):
    """设备仍是超级设备 USING 子项 → DeviceInUseError。"""
    device_repo = repos["device"]
    sd_repo = repos["super_device"]
    device_repo.reg_device(make_device("D1"))
    sd_repo.reg_super_device(make_super_device("SD1", devices=["D1"]))

    with pytest.raises(DeviceInUseError) as exc:
        device_repo.remove_device("D1")
    assert exc.value.super_device_using == 1

    # 从超级设备摘除后即可软删除
    sd_repo.remove_device("SD1", "D1")
    device_repo.remove_device("D1")
    assert device_repo.get_device("D1").state == DeviceState.REMOVED


def test_device_remove_blocked_by_volume(repos):
    """设备上仍有非 REMOVED 卷 → DeviceInUseError；卷删除后可移除。"""
    device_repo = repos["device"]
    volume_repo = repos["volume"]
    device_repo.reg_device(make_device("D1"))
    volume_repo.reg_volume(make_volume("V1", device_id="D1"))

    with pytest.raises(DeviceInUseError) as exc:
        device_repo.remove_device("D1")
    assert exc.value.volumes == 1

    volume_repo.remove_volume("V1")
    device_repo.remove_device("D1")
    assert device_repo.get_device("D1").state == DeviceState.REMOVED


def test_device_remove_missing_raises(repos):
    """删除不存在的设备 → ValueError。"""
    with pytest.raises(ValueError):
        repos["device"].remove_device("GHOST")


# ── VolumeRepository ──────────────────────────────────────────────


def test_volume_repository_rejects_unknown_device(repos):
    """device_id 既不是 Device 也不是 SuperDevice → ValueError。"""
    with pytest.raises(ValueError, match="既不是有效 Device"):
        repos["volume"].reg_volume(make_volume("V1", device_id="GHOST"))


def test_volume_repository_crud(repos):
    """卷登记/查询/更新/列表。"""
    volume_repo = repos["volume"]
    repos["device"].reg_device(make_device("D1"))
    volume = make_volume("V1", device_id="D1", file_system="exfat", info='{"a":1}')

    volume_repo.reg_volume(volume)
    assert volume_repo.is_exist("V1")
    got = volume_repo.get_volume("V1")
    assert got.file_system == "exfat"
    assert got.unique_mount_point == "/mnt/V1"
    assert got.device_id == "D1"

    volume_repo.update_volume("V1", capacity=99, name="renamed")
    got = volume_repo.get_volume("V1")
    assert got.capacity == 99
    assert got.name == "renamed"

    with pytest.raises(ValueError):
        volume_repo.update_volume("GHOST", capacity=1)


def test_volume_repository_update_serial_plain_rename(repos):
    """无子引用的卷 → update_serial 成功。"""
    volume_repo = repos["volume"]
    repos["device"].reg_device(make_device("D1"))
    volume_repo.reg_volume(make_volume("V1", device_id="D1"))

    volume_repo.update_serial("V1", "V1-NEW")
    assert volume_repo.is_exist("V1-NEW")
    assert not volume_repo.is_exist("V1")


def test_volume_repository_update_serial_cascades_to_children(repos):
    """卷带 file_locations/super_volume_structures 时改 serial → 级联迁移成功。"""
    volume_repo = repos["volume"]
    device_repo = repos["device"]
    file_repo = repos["file"]
    sv_repo = repos["super_volume"]
    device_repo.reg_device(make_device("D1"))
    volume_repo.reg_volume(make_volume("V1", device_id="D1"))
    volume_repo.reg_volume(make_volume("V2", device_id="D1"))

    new_file = NewFile(
        sha512="s", md5="m", size=1, add_time=datetime(2026, 1, 1),
        path="p", now_path="a.txt", now_volume="V1",
    )
    file_repo.reg_file(new_file)
    sv_repo.reg_super_volume(make_super_volume("SV1", volumes=["V1"]))

    volume_repo.update_serial("V1", "V1-NEW")

    assert volume_repo.is_exist("V1-NEW")
    with repos["session_factory"]() as session:
        assert session.query(FileLocationsModel).filter_by(
            now_volume="V1-NEW"
        ).count() == 1
        assert session.query(SuperVolumeStructureModel).filter_by(
            volume_id="V1-NEW"
        ).count() == 1


def test_volume_remove_blocked_by_files_and_super_volume(repos, session_factory):
    """卷上有文件或仍属超级卷 → VolumeInUseError。"""
    volume_repo = repos["volume"]
    file_repo = repos["file"]
    sv_repo = repos["super_volume"]
    repos["device"].reg_device(make_device("D1"))
    volume_repo.reg_volume(make_volume("V1", device_id="D1"))
    volume_repo.reg_volume(make_volume("V2", device_id="D1"))

    file_repo.reg_file(NewFile(
        sha512="s", md5="m", size=1, add_time=datetime(2026, 1, 1),
        path="p", now_path="a.txt", now_volume="V1",
    ))
    with pytest.raises(VolumeInUseError) as exc:
        volume_repo.remove_volume("V1")
    assert exc.value.files == 1

    # 文件标记 REMOVED 后解除文件占用
    with session_factory() as session:
        session.query(FileLocationsModel).filter_by(now_volume="V1").update(
            {"state": FileState.REMOVED}
        )
        session.commit()
    volume_repo.remove_volume("V1")
    assert volume_repo.get_volume("V1").state == VolumeState.REMOVED

    # V2 作为超级卷成员被占用
    sv_repo.reg_super_volume(make_super_volume("SV1", volumes=["V2"]))
    with pytest.raises(VolumeInUseError) as exc:
        volume_repo.remove_volume("V2")
    assert exc.value.super_volumes == 1

    sv_repo.remove_volumes("SV1", ["V2"])
    volume_repo.remove_volume("V2")
    assert volume_repo.get_volume("V2").state == VolumeState.REMOVED


def test_volume_remove_missing_raises(repos):
    """删除不存在的卷 → ValueError。"""
    with pytest.raises(ValueError):
        repos["volume"].remove_volume("GHOST")


# ── SuperDeviceRepository ─────────────────────────────────────────


def test_super_device_repository_registration_and_crud(repos):
    """注册超级设备 → 结构与列表返回子设备。"""
    sd_repo = repos["super_device"]
    repos["device"].reg_device(make_device("D1"))
    repos["device"].reg_device(make_device("D2"))

    sd_repo.reg_super_device(make_super_device("SD1", devices=["D1", "D2"]))
    assert sd_repo.is_exist("SD1")
    sd = sd_repo.get_super_device("SD1")
    assert sd.devices == ["D1", "D2"]
    assert sd.sdtype == "raidz"
    assert [s.serial for s in sd_repo.list_super_device()] == ["SD1"]

    sd_repo.update_super_device("SD1", name="R", capacity=5,
                                sdtype="raidz", state=SuperDeviceState.DANGER)
    sd = sd_repo.get_super_device("SD1")
    assert sd.name == "R"
    assert sd.capacity == 5
    assert sd.state == SuperDeviceState.DANGER


def test_super_device_repository_sub_validation(repos):
    """子项不存在/不可用/被占用 → 对应领域异常。"""
    sd_repo = repos["super_device"]
    device_repo = repos["device"]

    with pytest.raises(SubDeviceNotFoundError):
        sd_repo.reg_super_device(make_super_device("SD1", devices=["GHOST"]))

    device_repo.reg_device(make_device("D1", state=DeviceState.FAULT))
    with pytest.raises(SubDeviceUnavailableError):
        sd_repo.reg_super_device(make_super_device("SD2", devices=["D1"]))

    device_repo.reg_device(make_device("D2"))
    sd_repo.reg_super_device(make_super_device("SD3", devices=["D2"]))
    with pytest.raises(SubDeviceInUseError):
        sd_repo.reg_super_device(make_super_device("SD4", devices=["D2"]))


def test_super_device_replace_and_remove_child(repos, session_factory):
    """replace_device 记录 replaced_by；remove_device 标记 UNUSED。"""
    sd_repo = repos["super_device"]
    device_repo = repos["device"]
    for serial in ("D1", "D2", "D3"):
        device_repo.reg_device(make_device(serial))
    sd_repo.reg_super_device(make_super_device("SD1", devices=["D1", "D2"]))

    sd_repo.replace_device("SD1", "D1", "D3", datetime(2026, 1, 2))
    sd = sd_repo.get_super_device("SD1")
    assert sd.devices == ["D2", "D3"]

    with session_factory() as session:
        row = session.query(SuperDeviceStructureModel).filter_by(
            super_device_id="SD1", sub_device_id="D1"
        ).one()
        assert row.state == RelationState.UNUSED
        assert json.loads(row.info)["replaced_by"] == "D3"

    with pytest.raises(SubDeviceInUseError):
        sd_repo.replace_device("SD1", "D1", "D2", datetime(2026, 1, 3))

    sd_repo.remove_device("SD1", "D3")
    assert sd_repo.get_super_device("SD1").devices == ["D2"]


def test_super_device_add_device_exclusive(repos):
    """add_device 校验独占性。"""
    sd_repo = repos["super_device"]
    device_repo = repos["device"]
    for serial in ("D1", "D2"):
        device_repo.reg_device(make_device(serial))
    sd_repo.reg_super_device(make_super_device("SD1", devices=["D1"]))
    sd_repo.reg_super_device(make_super_device("SD2", devices=["D2"]))

    with pytest.raises(SubDeviceInUseError):
        sd_repo.add_device("SD1", "D2", datetime(2026, 1, 1))

    device_repo.reg_device(make_device("D3"))
    sd_repo.add_device("SD1", "D3", datetime(2026, 1, 1))
    assert sd_repo.get_super_device("SD1").devices == ["D1", "D3"]


def test_super_device_remove_blocked_by_volume(repos):
    """超级设备上仍有卷 → SuperDeviceInUseError。"""
    sd_repo = repos["super_device"]
    volume_repo = repos["volume"]
    device_repo = repos["device"]
    device_repo.reg_device(make_device("D1"))
    sd_repo.reg_super_device(make_super_device("SD1", devices=["D1"]))
    volume_repo.reg_volume(make_volume("V1", device_id="SD1"))

    with pytest.raises(SuperDeviceInUseError) as exc:
        sd_repo.remove_super_device("SD1")
    assert exc.value.volumes == 1

    volume_repo.remove_volume("V1")
    sd_repo.remove_super_device("SD1")
    assert sd_repo.get_super_device("SD1").state == SuperDeviceState.REMOVED


def test_super_device_update_serial_cascades(repos):
    """超级设备改名 → 结构父/子引用与卷归属级联。"""
    sd_repo = repos["super_device"]
    device_repo = repos["device"]
    volume_repo = repos["volume"]
    for serial in ("D1", "D2"):
        device_repo.reg_device(make_device(serial))
    sd_repo.reg_super_device(make_super_device("SD1", devices=["D1", "D2"]))
    sd_repo.reg_super_device(make_super_device("SD2", devices=["SD1"]))
    volume_repo.reg_volume(make_volume("V1", device_id="SD1"))

    sd_repo.update_super_device_serial("SD1", "SD1-NEW")

    assert sd_repo.is_exist("SD1-NEW")
    assert not sd_repo.is_exist("SD1")
    assert sd_repo.get_super_device("SD2").devices == ["SD1-NEW"]
    assert volume_repo.get_volume("V1").device_id == "SD1-NEW"


# ── SuperVolumeRepository ─────────────────────────────────────────


def _seed_volumes(repos, serials=("V1", "V2", "V3")):
    repos["device"].reg_device(make_device("D1"))
    for serial in serials:
        repos["volume"].reg_volume(make_volume(serial, device_id="D1"))


def test_super_volume_repository_crud(repos):
    """超级卷注册/查询/列表。"""
    _seed_volumes(repos, ("V1", "V2"))
    sv_repo = repos["super_volume"]
    sv_repo.reg_super_volume(make_super_volume("SV1", volumes=["V1", "V2"]))

    assert sv_repo.is_exist("SV1")
    got = sv_repo.get_super_volume("SV1")
    assert got.volumes == ["V1", "V2"]
    assert [s.serial for s in sv_repo.list_super_volume()] == ["SV1"]

    sv_repo.update_super_volume("SV1", name="copies", method="copy")
    assert sv_repo.get_super_volume("SV1").name == "copies"


def test_super_volume_add_and_remove_volumes(repos):
    """add_volumes 独占校验；remove_volumes 释放成员。"""
    _seed_volumes(repos, ("V1", "V2", "V3"))
    sv_repo = repos["super_volume"]
    sv_repo.reg_super_volume(make_super_volume("SV1", volumes=["V1"]))
    sv_repo.reg_super_volume(make_super_volume("SV2", volumes=["V2"]))

    # 卷已属于 SV2（USING）→ 拒绝
    from domain.storage.super_volume.structure import SuperVolumeStructure

    with pytest.raises(ValueError, match="已属于"):
        sv_repo.add_volumes([SuperVolumeStructure("SV1", "V2")])

    sv_repo.add_volumes([SuperVolumeStructure("SV1", "V3")])
    assert sv_repo.get_super_volume("SV1").volumes == ["V1", "V3"]

    with pytest.raises(ValueError, match="不是"):
        sv_repo.remove_volumes("SV1", ["V2"])

    sv_repo.remove_volumes("SV1", ["V1"])
    assert sv_repo.get_super_volume("SV1").volumes == ["V3"]


def test_super_volume_remove_releases_structures(repos):
    """remove_super_volume → 自身 REMOVED，成员关联转 UNUSED。"""
    _seed_volumes(repos)
    sv_repo = repos["super_volume"]
    sv_repo.reg_super_volume(make_super_volume("SV1", volumes=["V1", "V2"]))

    sv_repo.remove_super_volume("SV1")
    assert sv_repo.get_super_volume("SV1").state == SuperVolumeState.REMOVED
    with repos["session_factory"]() as session:
        rows = session.query(SuperVolumeStructureModel).filter_by(
            super_volume_id="SV1"
        ).all()
        assert len(rows) == 2
        assert {r.state for r in rows} == {RelationState.UNUSED}


def test_super_volume_update_serial_cascades(repos):
    """超级卷改名 → 结构父引用级联。"""
    _seed_volumes(repos)
    sv_repo = repos["super_volume"]
    sv_repo.reg_super_volume(make_super_volume("SV1", volumes=["V1"]))
    sv_repo.update_super_volume_serial("SV1", "SV1-NEW")

    assert sv_repo.is_exist("SV1-NEW")
    assert not sv_repo.is_exist("SV1")
    assert sv_repo.get_super_volume("SV1-NEW").volumes == ["V1"]


# ── FileRepository ────────────────────────────────────────────────


def test_file_repository_reg_and_list(repos):
    """reg_file 写 file_sources + file_locations；目录前缀查询。"""
    _seed_volumes(repos, ("V1",))
    file_repo = repos["file"]
    nf = NewFile(
        sha512="s1", md5="m1", size=10, add_time=datetime(2026, 1, 1),
        path="/outside/a.txt", now_path="dir/a.txt", now_volume="V1",
    )
    file_repo.reg_file(nf)

    with repos["session_factory"]() as session:
        assert session.query(FileSourcesModel).count() == 1
        assert session.query(FileLocationsModel).count() == 1

    rows = file_repo.list_by_volume_dir("V1", "dir")
    assert [r["now_path"] for r in rows] == ["dir/a.txt"]
    assert file_repo.list_by_volume_dir("V1", "other") == []


def test_file_repository_move_and_copy(repos):
    """move 删除源位置；copy 保留源新增目标；源缺失抛 LookupError。"""
    _seed_volumes(repos, ("V1", "V2"))
    file_repo = repos["file"]
    nf = NewFile(
        sha512="s1", md5="m1", size=10, add_time=datetime(2026, 1, 1),
        path="/p", now_path="dir/a.txt", now_volume="V1",
    )
    file_repo.reg_file(nf)

    file_repo.move_file("s1", "m1", "V1", "dir/a.txt", "V2", "moved/a.txt")
    with repos["session_factory"]() as session:
        assert session.query(FileLocationsModel).filter_by(now_volume="V1").count() == 0
        assert session.query(FileLocationsModel).filter_by(now_volume="V2").count() == 1

    file_repo.copy_file("s1", "m1", "V2", "moved/a.txt", "V1", "copy/a.txt")
    with repos["session_factory"]() as session:
        assert session.query(FileLocationsModel).count() == 2

    with pytest.raises(LookupError):
        file_repo.move_file("s", "m", "V1", "no-such", "V2", "x")


# ── state 字符串归一化 ────────────────────────────────────────────


def test_device_repo_normalizes_state_strings(repos):
    """设备 state 传值/名称字符串 → 归一为枚举落库并可读回。"""
    repo = repos["device"]
    repo.reg_device(make_device("D1", state="fault"))        # 值形式
    assert repo.get_device("D1").state == DeviceState.FAULT

    repo.update_device("D1", state="REMOVED")                # 名称形式
    assert repo.get_device("D1").state == DeviceState.REMOVED

    with pytest.raises(ValueError):
        repo.reg_device(make_device("D2", state="not-a-state"))


def test_volume_repo_normalizes_state_strings(repos):
    """卷 state 字符串 → 归一为枚举。"""
    repos["device"].reg_device(make_device("D1"))
    volume_repo = repos["volume"]
    volume_repo.reg_volume(make_volume("V1", device_id="D1", state="danger"))
    assert volume_repo.get_volume("V1").state == VolumeState.DANGER

    volume_repo.update_volume("V1", state="FAULT")
    assert volume_repo.get_volume("V1").state == VolumeState.FAULT


def test_super_device_repo_normalizes_state_strings(repos):
    """超级设备 state 字符串 → 归一为枚举。"""
    repos["device"].reg_device(make_device("D1"))
    sd_repo = repos["super_device"]
    sd_repo.reg_super_device(make_super_device("SD1", devices=["D1"], state="degrading"))
    assert sd_repo.get_super_device("SD1").state == SuperDeviceState.DEGRADING

    sd_repo.update_super_device("SD1", state="REMOVED")
    assert sd_repo.get_super_device("SD1").state == SuperDeviceState.REMOVED


def test_super_volume_repo_normalizes_state_strings(repos):
    """超级卷 state 字符串 → 归一为枚举。"""
    _seed_volumes(repos, ("V1",))
    sv_repo = repos["super_volume"]
    sv_repo.reg_super_volume(make_super_volume("SV1", volumes=["V1"], state="danger"))
    assert sv_repo.get_super_volume("SV1").state == SuperVolumeState.DANGER

    sv_repo.update_super_volume("SV1", state="UNKNOWN")
    assert sv_repo.get_super_volume("SV1").state == SuperVolumeState.UNKNOWN


def test_file_repo_normalizes_state_strings(repos):
    """文件 state 字符串 → file_sources/file_locations 均归一为枚举。"""
    _seed_volumes(repos, ("V1",))
    file_repo = repos["file"]
    file_repo.reg_file(NewFile(
        sha512="s", md5="m", size=1, add_time=datetime(2026, 1, 1),
        path="p", now_path="a.txt", now_volume="V1", state="damaged",
    ))
    with repos["session_factory"]() as session:
        assert session.query(FileSourcesModel).one().state == FileState.DAMAGED
        assert session.query(FileLocationsModel).one().state == FileState.DAMAGED
