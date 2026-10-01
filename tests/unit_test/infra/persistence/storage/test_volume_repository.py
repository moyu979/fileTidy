# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/storage/volume_repository.py —— VolumeRepository 隔离单测。

目的（测什么）：
- `reg_volume` 的 device_id 兜底校验（必须是已存在的 Device 或 SuperDevice）、
  `unique_mount_point=None` 落库为字符串 "None"、`info=None` 落库为空串；
- `get_volume` / `list_volumes` / `is_exist`（字符串或 Volume 对象）的字段往返；
- `update_volume` 的字段更新、state 归一化、不存在时 ValueError；
- `update_serial` 的主键迁移与对 file_locations.now_volume、super_volume_structures.volume_id 的级联；
- `remove_volume` 的软删除与占用保护（VolumeInUseError：文件占用 / 仍属超级卷）。

输入：`tmp_path` 下每个用例独占的临时 SQLite 库 + `_helpers` 构造的领域对象。

期望输出：查询结果、数据库行与异常类型符合仓储 docstring。
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from domain.storage.super_device.enum import RelationState
from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.errors import VolumeInUseError
from domain.storage.volume.repo import VolumeRepositoryABC
from infra.persistence.models import (
    FileLocationsModel,
    SuperVolumeStructureModel,
    VolumeModel,
)
from domain.storage.file.enum import FileState
from tests.unit_test.infra.persistence import _helpers as H


@pytest.fixture
def db(tmp_path):
    """每个用例独占的临时 SQLite 库（仅建表）。"""
    handle = H.new_db(tmp_path / "volume.db")
    yield handle
    handle.dispose()


@pytest.fixture
def repo(db):
    """绑定该库的 VolumeRepository。"""
    return db.repos["volume"]


@pytest.fixture
def device(db):
    """一个已登记的物理设备（卷的挂载对象）。"""
    device = H.make_device("D1")
    db.repos["device"].reg_device(device)
    return device


# ── 构造与注册 ────────────────────────────────────────────────────


def test_repository_is_abc_implementation(db, repo):
    """输入 新建仓储 → 期望输出 是 VolumeRepositoryABC 实例且复用同一会话工厂。"""
    assert isinstance(repo, VolumeRepositoryABC)
    assert repo.session_factory is db.factory


def test_reg_volume_requires_known_device_or_super_device(db, repo):
    """输入 device_id 不存在 → 期望输出 ValueError 且未落库。"""
    with pytest.raises(ValueError, match="既不是有效 Device"):
        repo.reg_volume(H.make_volume("V1", device_id="GHOST"))

    assert repo.is_exist("V1") is False


def test_reg_volume_accepts_super_device_as_owner(db, repo, device):
    """输入 volume.device_id 指向已存在的超级设备 → 期望输出 登记成功。"""
    db.repos["super_device"].reg_super_device(
        H.make_super_device("SD1", devices=["D1"])
    )

    repo.reg_volume(H.make_volume("V1", device_id="SD1"))

    assert repo.is_exist("V1") is True


def test_reg_volume_then_get_round_trip(db, repo, device):
    """输入 登记 exfat 卷 → 期望输出 读回字段与写入一致。"""
    repo.reg_volume(
        H.make_volume(
            "V1",
            device_id="D1",
            file_system="exfat",
            capacity=2048,
            info='{"a": 1}',
        )
    )

    got = repo.get_volume("V1")

    assert isinstance(got, Volume)
    assert got.serial == "V1"
    assert got.device_id == "D1"
    assert got.name == "V1"
    assert got.file_system == "exfat"
    assert got.capacity == 2048
    assert got.info == '{"a": 1}'
    assert got.unique_mount_point == "/mnt/V1"
    assert got.state is VolumeState.HEALTHY
    assert got.add_time == H.FIXED_TIME
    assert got.volume_path is None
    assert H.count(db, VolumeModel) == 1


def test_reg_volume_writes_mount_point_none_as_text(db, repo, device):
    """输入 unique_mount_point=None 且 file_system/info 为 None → 期望输出 落库为 'None' / '' / ''。"""
    repo.reg_volume(
        H.make_volume(
            "V1",
            device_id="D1",
            unique_mount_point=None,
            file_system=None,
            info=None,
        )
    )

    got = repo.get_volume("V1")

    assert got.unique_mount_point == "None"
    assert got.file_system == ""
    assert got.info == ""


def test_get_volume_missing_returns_none(repo):
    """输入 不存在的 serial → 期望输出 None。"""
    assert repo.get_volume("GHOST") is None


def test_is_exist_accepts_string_and_volume(db, repo, device):
    """输入 未登记/已登记的 serial 与 Volume 对象 → 期望输出 False / True。"""
    assert repo.is_exist("V1") is False
    assert repo.is_exist(H.make_volume("V1")) is False

    repo.reg_volume(H.make_volume("V1", device_id="D1"))

    assert repo.is_exist("V1") is True
    assert repo.is_exist(H.make_volume("V1")) is True


def test_list_volumes_returns_all_registered(db, repo, device):
    """输入 空库/登记两卷 → 期望输出 [] / 两卷；带默认数据的库含 EXTERNAL_VOLUME。"""
    assert repo.list_volumes() == []

    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    repo.reg_volume(H.make_volume("V2", device_id="D1"))

    assert sorted(v.serial for v in repo.list_volumes()) == ["V1", "V2"]


def test_list_volumes_includes_default_placeholder(tmp_path):
    """输入 已填充默认数据的库 → 期望输出 列表包含 EXTERNAL_VOLUME 占位卷。"""
    handle = H.new_db(tmp_path / "seeded.db", with_defaults=True)
    try:
        serials = [v.serial for v in handle.repos["volume"].list_volumes()]
        assert serials == ["EXTERNAL_VOLUME"]
    finally:
        handle.dispose()


def test_reg_volume_duplicate_serial_raises_integrity_error(db, repo, device):
    """输入 登记已存在的 serial → 期望输出 IntegrityError 且行数不变。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))

    with pytest.raises(IntegrityError):
        repo.reg_volume(H.make_volume("V1", device_id="D1", file_system="exfat"))

    assert H.count(db, VolumeModel) == 1


# ── 更新 ──────────────────────────────────────────────────────────


def test_update_volume_updates_given_fields_only(db, repo, device):
    """输入 只更新 capacity 与 name → 期望输出 两字段生效、其余保持原值。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1", file_system="exfat"))

    repo.update_volume("V1", capacity=99, name="renamed")

    got = repo.get_volume("V1")
    assert got.capacity == 99
    assert got.name == "renamed"
    assert got.file_system == "exfat"
    assert got.device_id == "D1"


def test_update_volume_missing_raises_value_error(repo):
    """输入 更新不存在的卷 → 期望输出 ValueError。"""
    with pytest.raises(ValueError, match="not found"):
        repo.update_volume("GHOST", capacity=1)


def test_update_volume_coerces_state_strings(db, repo, device):
    """输入 state 传 'danger' 与 'FAULT' → 期望输出 落库为对应枚举成员。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))

    repo.update_volume("V1", state="danger")
    assert repo.get_volume("V1").state is VolumeState.DANGER

    repo.update_volume("V1", state="FAULT")
    assert repo.get_volume("V1").state is VolumeState.FAULT


def test_update_volume_invalid_state_raises(db, repo, device):
    """输入 state='bogus' → 期望输出 ValueError 且原状态不变。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))

    with pytest.raises(ValueError, match="不是 VolumeState 的合法状态"):
        repo.update_volume("V1", state="bogus")

    assert repo.get_volume("V1").state is VolumeState.HEALTHY


# ── 主键迁移 ──────────────────────────────────────────────────────


def test_update_serial_plain_rename(db, repo, device):
    """输入 无子引用的卷改名 → 期望输出 新 serial 存在、旧 serial 消失。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1", file_system="exfat"))

    repo.update_serial("V1", "V1-NEW")

    assert repo.is_exist("V1-NEW") is True
    assert repo.is_exist("V1") is False
    assert repo.get_volume("V1-NEW").file_system == "exfat"


def test_update_serial_same_serial_is_noop(db, repo, device):
    """输入 新旧 serial 相同 → 期望输出 提前返回，记录仍在。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))

    repo.update_serial("V1", "V1")

    assert repo.is_exist("V1") is True


def test_update_serial_cascades_to_files_and_structures(db, repo, device):
    """输入 卷被文件位置与超级卷关联引用 → 期望输出 两处引用一并迁移到新 serial。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    db.repos["file"].reg_file(H.make_new_file(now_volume="V1", now_path="dir/a.txt"))
    sv_repo = db.repos["super_volume"]
    sv_repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    repo.update_serial("V1", "V1-NEW")

    assert repo.is_exist("V1-NEW") is True
    assert repo.is_exist("V1") is False
    assert H.count(db, FileLocationsModel) == 1
    assert H.count(db, SuperVolumeStructureModel) == 1
    with db.factory() as session:
        assert (
            session.query(FileLocationsModel)
            .filter(FileLocationsModel.now_volume == "V1-NEW")
            .count()
            == 1
        )
        assert (
            session.query(SuperVolumeStructureModel)
            .filter(SuperVolumeStructureModel.volume_id == "V1-NEW")
            .count()
            == 1
        )
    assert sv_repo.get_super_volume("SV1").volumes == ["V1-NEW"]


def test_update_serial_missing_raises_value_error(repo):
    """输入 迁移不存在的卷 → 期望输出 ValueError。"""
    with pytest.raises(ValueError, match="not found"):
        repo.update_serial("GHOST", "NEW")


# ── 软删除与占用保护 ──────────────────────────────────────────────


def test_remove_volume_marks_removed_and_keeps_row(db, repo, device):
    """输入 无引用的卷 → 期望输出 state 变 REMOVED，行仍保留。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))

    repo.remove_volume("V1")

    assert repo.get_volume("V1").state is VolumeState.REMOVED
    assert H.count(db, VolumeModel) == 1


def test_remove_volume_missing_raises_value_error(repo):
    """输入 删除不存在的卷 → 期望输出 ValueError。"""
    with pytest.raises(ValueError, match="not found"):
        repo.remove_volume("GHOST")


def test_remove_volume_blocked_by_files_then_allowed(db, repo, device):
    """输入 卷上仍有非 REMOVED 文件位置 → 期望输出 VolumeInUseError(files=1)；标 REMOVED 后可删。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    db.repos["file"].reg_file(H.make_new_file(now_volume="V1", now_path="dir/a.txt"))

    with pytest.raises(VolumeInUseError) as excinfo:
        repo.remove_volume("V1")

    assert excinfo.value.serial == "V1"
    assert excinfo.value.files == 1
    assert excinfo.value.super_volumes == 0
    assert repo.get_volume("V1").state is VolumeState.HEALTHY

    with db.factory() as session:
        session.query(FileLocationsModel).filter(
            FileLocationsModel.now_volume == "V1"
        ).update({"state": FileState.REMOVED})
        session.commit()

    repo.remove_volume("V1")
    assert repo.get_volume("V1").state is VolumeState.REMOVED


def test_remove_volume_blocked_by_super_volume_then_allowed(db, repo, device):
    """输入 卷仍是超级卷 USING 成员 → 期望输出 VolumeInUseError(super_volumes=1)；释放后可删。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    sv_repo = db.repos["super_volume"]
    sv_repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    with pytest.raises(VolumeInUseError) as excinfo:
        repo.remove_volume("V1")

    assert excinfo.value.super_volumes == 1
    assert excinfo.value.files == 0
    with db.factory() as session:
        row = session.query(SuperVolumeStructureModel).one()
        assert row.state is RelationState.USING

    sv_repo.remove_volumes("SV1", ["V1"])
    repo.remove_volume("V1")

    assert repo.get_volume("V1").state is VolumeState.REMOVED
