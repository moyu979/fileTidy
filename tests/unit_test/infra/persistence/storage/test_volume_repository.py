# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/storage/volume_repository.py —— VolumeRepository 隔离单测。

目的（测什么）：
- `reg_volume` 的 device_id 兜底校验（必须是已存在的 Device 或 SuperDevice）、
  `unique_mount_point=None` 由列默认落库为 "/unknown"、`file_system`/`info`/`state` 为 None 时落库为空串/UNKNOWN；
- 改成已存在 / 已移除的 serial → 抛领域异常（AlreadyRegistered / AlreadyRemoved）且事务回滚；
- `get_volume` / `list_volumes` / `is_exist`（字符串或 Volume 对象）的字段往返；
- `update_volume` 的字段更新、state 归一化、None 视为「未提供」保持原值、不存在时 ValueError、
  拒绝未知字段 / 改 serial / 置 REMOVED；
- `update_serial` 的主键迁移与对 file_locations.now_volume、super_volume_structures.volume_id 的级联；
- `remove_volume` 的软删除与占用保护（VolumeInUseError：文件占用 / 仍属超级卷）；
- `revive_volume`：REMOVED → UNKNOWN，并校验挂载对象仍存在且可用。

输入：`tmp_path` 下每个用例独占的临时 SQLite 库 + `_helpers` 构造的领域对象。

期望输出：查询结果、数据库行与异常类型符合仓储 docstring。
"""

from __future__ import annotations

from datetime import datetime

import pytest

from domain.storage.device.enum import DeviceState
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_volume.enum import SuperVolumeRelationState
from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.errors import (
    VolumeAlreadyRegisteredError,
    VolumeAlreadyRemovedError,
    VolumeInUseError,
    VolumeNotFoundError,
    VolumeNotRemovedError,
)
from domain.storage.volume.repo import VolumeRepositoryABC
from infra.persistence.models import (
    FileLocationsModel,
    SuperVolumeStructureModel,
    VolumeModel,
)
from domain.storage.file.enum import FileState
from infra.persistence.storage.volume_repository import VolumeRepository
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


def test_reg_volume_rejects_removed_device(db, repo):
    """输入 device_id 指向已 REMOVED 的设备 → 期望输出 ValueError（不可用）且未落库。"""
    db.repos["device"].reg_device(H.make_device("D1", state=DeviceState.REMOVED))

    with pytest.raises(ValueError, match="不可用状态"):
        repo.reg_volume(H.make_volume("V1", device_id="D1"))

    assert repo.is_exist("V1") is False


def test_reg_volume_rejects_fault_device(db, repo):
    """输入 device_id 指向 FAULT 设备 → 期望输出 ValueError（不可用）。"""
    db.repos["device"].reg_device(H.make_device("D1", state=DeviceState.FAULT))

    with pytest.raises(ValueError, match="不可用状态 FAULT"):
        repo.reg_volume(H.make_volume("V1", device_id="D1"))


def test_reg_volume_rejects_removed_super_device(db, repo, device):
    """输入 device_id 指向已 REMOVED 的超级设备 → 期望输出 ValueError（不可用）。"""
    db.repos["super_device"].reg_super_device(
        H.make_super_device("SD1", devices=["D1"], state=SuperDeviceState.REMOVED)
    )

    with pytest.raises(ValueError, match="不可用状态"):
        repo.reg_volume(H.make_volume("V1", device_id="SD1"))


def test_update_volume_rejects_removed_device(db, repo, device):
    """输入 把卷改挂到 REMOVED 设备 → 期望输出 ValueError，且 device_id 保持原值。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    db.repos["device"].reg_device(H.make_device("D2", state=DeviceState.REMOVED))

    with pytest.raises(ValueError, match="不可用状态"):
        repo.update_volume("V1", device_id="D2")

    assert repo.get_volume("V1").device_id == "D1"


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


def test_reg_volume_fills_none_columns_from_defaults(db, repo, device):
    """输入 unique_mount_point/file_system/info 均为 None → 期望输出 落库为列默认 '/unknown' / '' / ''。"""
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

    assert got.unique_mount_point == "/unknown"
    assert got.file_system == ""
    assert got.info == ""


def test_reg_volume_none_state_falls_back_to_column_default(db, repo, device):
    """输入 state=None → 期望输出 落库为列默认 UNKNOWN（不留 NULL）。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1", state=None))

    assert repo.get_volume("V1").state is VolumeState.UNKNOWN


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


def test_get_volume_excludes_removed_by_default(db, repo, device):
    """输入 已软删除的卷 → 期望输出 默认 None；exclude_removed=False 时返回 REMOVED 卷。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    repo.remove_volume("V1")

    assert repo.get_volume("V1") is None
    assert repo.get_volume("V1", exclude_removed=False).state is VolumeState.REMOVED


def test_list_volumes_excludes_removed_by_default(db, repo, device):
    """输入 一正常卷 + 一已删除卷 → 期望输出 默认只剩正常卷；False 时两卷都在。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    repo.reg_volume(H.make_volume("V2", device_id="D1"))
    repo.remove_volume("V2")

    assert [v.serial for v in repo.list_volumes()] == ["V1"]
    assert sorted(v.serial for v in repo.list_volumes(exclude_removed=False)) == [
        "V1",
        "V2",
    ]


def test_reg_volume_duplicate_serial_raises_already_registered(db, repo, device):
    """输入 登记已存在的 serial（非 REMOVED）→ 期望输出 VolumeAlreadyRegisteredError 且行数不变。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1", file_system="exfat"))

    with pytest.raises(VolumeAlreadyRegisteredError) as excinfo:
        repo.reg_volume(H.make_volume("V1", device_id="D1", file_system="ntfs"))

    assert excinfo.value.serial == "V1"
    assert excinfo.value.state is VolumeState.HEALTHY
    assert H.count(db, VolumeModel) == 1


def test_reg_volume_duplicate_removed_serial_reports_removed(db, repo, device):
    """输入 serial 已被软删的登记行占用 → 期望输出 VolumeAlreadyRemovedError（上层据此提示 revive）。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    repo.remove_volume("V1")

    with pytest.raises(VolumeAlreadyRemovedError) as excinfo:
        repo.reg_volume(H.make_volume("V1", device_id="D1"))

    assert excinfo.value.serial == "V1"
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
    with pytest.raises(VolumeNotFoundError):
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


def test_update_volume_none_keeps_original(db, repo, device):
    """输入 state/capacity/info 传 None → 期望输出 视为「未提供」，字段保持原值而非写 NULL。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1", capacity=2048))

    repo.update_volume("V1", state=None, capacity=None, info=None)

    got = repo.get_volume("V1")
    assert got.state is VolumeState.HEALTHY
    assert got.capacity == 2048
    assert got.info == ""


def test_update_volume_rejects_removed_state(db, repo, device):
    """输入 state='REMOVED' → 期望输出 ValueError 且原状态不变（软删除必须走 remove_volume）。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))

    with pytest.raises(ValueError, match="REMOVED"):
        repo.update_volume("V1", state="REMOVED")

    assert repo.get_volume("V1").state is VolumeState.HEALTHY


def test_update_volume_rejects_unknown_field(db, repo, device):
    """输入 拼错的字段名 → 期望输出 ValueError（不再静默无效）且原值不变。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))

    with pytest.raises(ValueError, match="不支持更新字段"):
        repo.update_volume("V1", nam="x")  # 拼错 name

    assert repo.get_volume("V1").name == "V1"


def test_update_volume_rejects_serial_change(db, repo, device):
    """输入 试图用 update_volume 改序列号 → 期望输出 ValueError 且 serial 不变（须走 update_serial）。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))

    with pytest.raises(ValueError, match="update_serial"):
        repo.update_volume("V1", serial="V1-X")

    assert repo.is_exist("V1") is True
    assert repo.is_exist("V1-X") is False


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
    H.register_file(db.repos["file"], H.make_new_file(now_volume="V1", now_path="dir/a.txt"))
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
    with pytest.raises(VolumeNotFoundError):
        repo.update_serial("GHOST", "NEW")


def test_update_serial_to_existing_serial_raises_and_rolls_back(db, repo, device):
    """输入 把 V1 改名为已存在的 V2 → 期望输出 VolumeAlreadyRegisteredError 且两张记录都还在。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    repo.reg_volume(H.make_volume("V2", device_id="D1"))

    with pytest.raises(VolumeAlreadyRegisteredError):
        repo.update_serial("V1", "V2")

    assert sorted(v.serial for v in repo.list_volumes()) == ["V1", "V2"]


def test_update_serial_to_removed_serial_raises(db, repo, device):
    """输入 把 V1 改名为一条 REMOVED 墓碑占用的 serial → 期望输出 VolumeAlreadyRemovedError。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    repo.reg_volume(H.make_volume("V2", device_id="D1"))
    repo.remove_volume("V2")

    with pytest.raises(VolumeAlreadyRemovedError):
        repo.update_serial("V1", "V2")

    # 事务回滚：V1 仍在，V2 墓碑仍占位
    assert repo.is_exist("V1") is True
    assert repo.is_exist("V2") is True
    assert repo.get_volume("V2") is None


# ── 软删除与占用保护 ──────────────────────────────────────────────


def test_remove_volume_marks_removed_and_keeps_row(db, repo, device):
    """输入 无引用的卷 → 期望输出 state 变 REMOVED，行仍保留。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))

    repo.remove_volume("V1")

    assert repo.get_volume("V1", exclude_removed=False).state is VolumeState.REMOVED
    assert H.count(db, VolumeModel) == 1


def test_remove_volume_missing_raises_value_error(repo):
    """输入 删除不存在的卷 → 期望输出 ValueError。"""
    with pytest.raises(VolumeNotFoundError):
        repo.remove_volume("GHOST")


def test_remove_volume_blocked_by_files_then_allowed(db, repo, device):
    """输入 卷上仍有非 REMOVED 文件位置 → 期望输出 VolumeInUseError(files=1)；标 REMOVED 后可删。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    H.register_file(db.repos["file"], H.make_new_file(now_volume="V1", now_path="dir/a.txt"))

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
    assert repo.get_volume("V1", exclude_removed=False).state is VolumeState.REMOVED


def test_remove_volume_blocked_by_super_volume_then_allowed(db, repo, device):
    """输入 卷仍是超级卷 USING 成员 → 期望输出 VolumeInUseError(super_volumes=1)；换下后可删。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    repo.reg_volume(H.make_volume("V3", device_id="D1"))
    sv_repo = db.repos["super_volume"]
    sv_repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    with pytest.raises(VolumeInUseError) as excinfo:
        repo.remove_volume("V1")

    assert excinfo.value.super_volumes == 1
    assert excinfo.value.files == 0
    with db.factory() as session:
        row = session.query(SuperVolumeStructureModel).one()
        assert row.state is SuperVolumeRelationState.USING

    sv_repo.replace_volume("SV1", "V1", "V3", datetime.now())
    repo.remove_volume("V1")

    assert repo.get_volume("V1", exclude_removed=False).state is VolumeState.REMOVED


# ── 复活（REMOVED → UNKNOWN） ──────────────────────────────────────


def test_remove_volume_already_removed_raises(db, repo, device):
    """输入 对已 REMOVED 的卷再删一次 → 期望输出 VolumeAlreadyRemovedError。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    repo.remove_volume("V1")

    with pytest.raises(VolumeAlreadyRemovedError) as excinfo:
        repo.remove_volume("V1")

    assert excinfo.value.serial == "V1"


def test_revive_volume_restores_unknown(db, repo, device):
    """输入 已 REMOVED 的卷 → 期望输出 state 置回 UNKNOWN，其余字段保持不变。"""
    repo.reg_volume(
        H.make_volume("V1", device_id="D1", name="卷A", file_system="exfat", capacity=512)
    )
    repo.remove_volume("V1")

    repo.revive_volume("V1")

    got = repo.get_volume("V1")
    assert got is not None
    assert got.state is VolumeState.UNKNOWN
    assert got.name == "卷A"
    assert got.file_system == "exfat"
    assert got.capacity == 512


def test_revive_volume_missing_raises(repo):
    """输入 复活不存在的卷 → 期望输出 ValueError(not found)。"""
    with pytest.raises(VolumeNotFoundError):
        repo.revive_volume("GHOST")


def test_revive_volume_not_removed_raises(db, repo, device):
    """输入 复活未处于 REMOVED 的卷 → 期望输出 VolumeNotRemovedError 且状态不变。"""
    repo.reg_volume(H.make_volume("V1", device_id="D1", state=VolumeState.HEALTHY))

    with pytest.raises(VolumeNotRemovedError) as excinfo:
        repo.revive_volume("V1")

    assert excinfo.value.state is VolumeState.HEALTHY
    assert repo.get_volume("V1").state is VolumeState.HEALTHY


def test_revive_volume_rejects_removed_mount_target(db, repo, device):
    """输入 卷被软删后其挂载设备也被移除 → 期望输出 ValueError 且卷保持 REMOVED。

    卷被软删后不再阻塞其 device 的移除（remove_device 只看 state != REMOVED 的卷），
    因此复活前必须复检挂载对象仍然可用，否则会造出悬空的可用卷。
    """
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    repo.remove_volume("V1")
    db.repos["device"].remove_device("D1")

    with pytest.raises(ValueError, match="不可用状态"):
        repo.revive_volume("V1")

    assert repo.get_volume("V1", exclude_removed=False).state is VolumeState.REMOVED


def test_revive_volume_rejects_missing_mount_target(db, repo):
    """输入 挂载对象既不是 Device 也不是 SuperDevice → 期望输出 ValueError 且卷保持 REMOVED。"""
    db.repos["device"].reg_device(H.make_device("D1"))
    repo.reg_volume(H.make_volume("V1", device_id="D1"))
    repo.remove_volume("V1")
    with db.factory() as session:
        session.query(VolumeModel).filter_by(serial="V1").update({"device_id": "GHOST"})
        session.commit()

    with pytest.raises(ValueError, match="既不是有效 Device"):
        repo.revive_volume("V1")

    assert repo.get_volume("V1", exclude_removed=False).state is VolumeState.REMOVED


def test_revive_volume_accepts_available_super_device_as_target(db, repo):
    """输入 卷挂在可用的 SuperDevice 上 → 期望输出 复活成功。"""
    db.repos["device"].reg_device(H.make_device("D1"))
    db.repos["super_device"].reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    repo.reg_volume(H.make_volume("V1", device_id="SD1"))
    repo.remove_volume("V1")

    repo.revive_volume("V1")

    assert repo.get_volume("V1").state is VolumeState.UNKNOWN


# ── 私有工具与静态方法 ────────────────────────────────────────────


def test_model_to_dict_is_static_and_complete():
    """输入 内存构造的模型行 → 期望输出 字段齐全且值原样透传。"""
    model = VolumeModel(
        serial="V1",
        device_id="D1",
        name="n",
        state=VolumeState.HEALTHY,
        capacity=3,
        unique_mount_point="/mnt/V1",
        file_system="exfat",
        info="i",
    )

    assert VolumeRepository._model_to_dict(model) == {
        "serial": "V1",
        "device_id": "D1",
        "name": "n",
        "add_time": None,
        "last_check_time": None,
        "state": VolumeState.HEALTHY,
        "capacity": 3,
        "unique_mount_point": "/mnt/V1",
        "file_system": "exfat",
        "info": "i",
    }
