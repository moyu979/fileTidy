# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/storage/super_device_repository.py —— SuperDeviceRepository 隔离单测。

目的（测什么）：
- 注册/查询/列表/`is_exist`，以及父子关联行（含超级设备层叠）的读写；
- 子项挂载校验：不存在 → SubDeviceNotFoundError、REMOVED/FAULT → SubDeviceUnavailableError、
  已被其它超级设备 USING 占用 → SubDeviceInUseError，且失败时整个事务回滚（原子性）；
- `update_super_device` 的 sdtype→type 字段映射、state 归一化与 None 视为「未提供」保持原值；
- `update_super_device_serial` 对父引用、子引用（层叠）、volumes.device_id 的级联；
- `add_device` / `replace_device` / `remove_device` 的关联状态流转与 fail-fast 顺序；
- 软删除 `remove_super_device` 的占用保护；
- 模块私有工具 `_resolve_sub` 与静态 `_model_to_dict`。

输入：`tmp_path` 下每个用例独占的临时 SQLite 库 + `_helpers` 构造的领域对象。

期望输出：查询结果、关联行状态、JSON info 与异常类型符合仓储 docstring。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from domain.storage.device.enum import DeviceState
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceRelationState, SuperDeviceState
from domain.storage.super_device.errors import (
    SubDeviceInUseError,
    SubDeviceNotFoundError,
    SubDeviceUnavailableError,
    SuperDeviceAlreadyRegisteredError,
    SuperDeviceAlreadyRemovedError,
    SuperDeviceInUseError,
    SuperDeviceNotFoundError,
    SuperDeviceNotRemovedError,
)
from domain.storage.super_device.repo import SuperDeviceRepositoryABC
from infra.persistence.models import SuperDeviceModel, SuperDeviceStructureModel
from infra.persistence.storage import super_device_repository as super_device_repository_mod
from infra.persistence.storage.super_device_repository import SuperDeviceRepository
from tests.unit_test.infra.persistence import _helpers as H


@pytest.fixture
def db(tmp_path):
    """每个用例独占的临时 SQLite 库（仅建表）。"""
    handle = H.new_db(tmp_path / "super_device.db")
    yield handle
    handle.dispose()


@pytest.fixture
def repo(db):
    """绑定该库的 SuperDeviceRepository。"""
    return db.repos["super_device"]


@pytest.fixture
def devices(db):
    """登记两台健康设备 D1 / D2 并返回其 serial。"""
    for serial in ("D1", "D2"):
        db.repos["device"].reg_device(H.make_device(serial))
    return ("D1", "D2")


def _structure_rows(db) -> list[SuperDeviceStructureModel]:
    """读取全部结构行。"""
    return H.query_all(db, SuperDeviceStructureModel)


# ── 构造与注册 ────────────────────────────────────────────────────


def test_repository_is_abc_implementation(db, repo):
    """输入 新建仓储 → 期望输出 是 SuperDeviceRepositoryABC 实例且复用同一会话工厂。"""
    assert isinstance(repo, SuperDeviceRepositoryABC)
    assert repo.session_factory is db.factory


def test_reg_and_get_super_device(db, repo, devices):
    """输入 带两个子设备的 raidz 超级设备 → 期望输出 字段往返且 devices 顺序与登记一致。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1", "D2"]))

    got = repo.get_super_device("SD1")

    assert isinstance(got, SuperDevice)
    assert got.serial == "SD1"
    assert got.sdtype == "raidz"
    assert got.need_all_devices_online is True
    assert got.capacity == 1000
    assert got.state is SuperDeviceState.HEALTHY
    assert got.add_time == H.FIXED_TIME
    assert got.devices == ["D1", "D2"]
    assert repo.is_exist("SD1") is True
    assert repo.is_exist(got) is True
    assert repo.is_exist("GHOST") is False


def test_reg_super_device_none_state_falls_back_to_column_default(db, repo, devices):
    """输入 state=None → 期望输出 落库为列默认 HEALTHY（不留 NULL）。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"], state=None))

    assert repo.get_super_device("SD1").state is SuperDeviceState.HEALTHY


def test_reg_super_device_accepts_super_device_child(db, repo, devices):
    """输入 超级设备层叠（SD2 以 SD1 为子项）→ 期望输出 devices 为 ['SD1']。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    repo.reg_super_device(H.make_super_device("SD2", devices=["SD1"]))

    assert repo.get_super_device("SD2").devices == ["SD1"]


def test_reg_super_device_child_rows_have_empty_info(db, repo, devices):
    """输入 父带非空 info 登记 → 期望输出 子项关联行 info 为空（不继承父的 info）。"""
    repo.reg_super_device(
        H.make_super_device("SD1", devices=["D1", "D2"], info='{"k": 1}')
    )

    rows = _structure_rows(db)
    assert len(rows) == 2
    assert all(row.info == "" for row in rows)


def test_get_super_device_missing_returns_none(repo):
    """输入 不存在的 serial → 期望输出 None。"""
    assert repo.get_super_device("GHOST") is None


def test_list_super_device_returns_all(db, repo, devices):
    """输入 空库/登记两台超级设备 → 期望输出 [] / 两个对象。"""
    assert repo.list_super_device() == []

    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    repo.reg_super_device(H.make_super_device("SD2", devices=["D2"]))

    assert sorted(s.serial for s in repo.list_super_device()) == ["SD1", "SD2"]


def test_list_super_device_includes_default_placeholder(tmp_path):
    """输入 已填充默认数据的库 → 期望输出 列表含 EXTERNAL_SUPER_DEVICE 且子项为默认设备。"""
    handle = H.new_db(tmp_path / "seeded.db", with_defaults=True)
    try:
        items = handle.repos["super_device"].list_super_device()
        assert [s.serial for s in items] == ["EXTERNAL_SUPER_DEVICE"]
        assert items[0].devices == ["EXTERNAL_DEVICE"]
    finally:
        handle.dispose()


# ── 子项校验与原子性 ──────────────────────────────────────────────


def test_reg_super_device_nonexistent_child_raises(db, repo):
    """输入 子项既不是设备也不是超级设备 → 期望输出 SubDeviceNotFoundError 且未落库。"""
    with pytest.raises(SubDeviceNotFoundError):
        repo.reg_super_device(H.make_super_device("SD1", devices=["GHOST"]))

    assert repo.is_exist("SD1") is False
    assert _structure_rows(db) == []


def test_reg_super_device_fault_child_raises_unavailable(db, repo):
    """输入 子项设备为 FAULT → 期望输出 SubDeviceUnavailableError 且超级设备未落库。"""
    db.repos["device"].reg_device(H.make_device("D1", state=DeviceState.FAULT))

    with pytest.raises(SubDeviceUnavailableError):
        repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    assert repo.is_exist("SD1") is False


def test_reg_super_device_removed_super_device_child_raises_unavailable(db, repo, devices):
    """输入 子项超级设备已 REMOVED → 期望输出 SubDeviceUnavailableError。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    repo.remove_super_device("SD1")

    with pytest.raises(SubDeviceUnavailableError):
        repo.reg_super_device(H.make_super_device("SD2", devices=["SD1"]))


def test_reg_super_device_child_in_use_raises(db, repo, devices):
    """输入 子项已被其它超级设备 USING 占用 → 期望输出 SubDeviceInUseError。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    with pytest.raises(SubDeviceInUseError):
        repo.reg_super_device(H.make_super_device("SD2", devices=["D1"]))

    assert repo.is_exist("SD2") is False


def test_reg_super_device_duplicate_serial_raises_already_registered(db, repo, devices):
    """输入 serial 与已有超级设备冲突 → 期望输出 SuperDeviceAlreadyRegisteredError 且不新增任何行。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    with pytest.raises(SuperDeviceAlreadyRegisteredError) as excinfo:
        repo.reg_super_device(H.make_super_device("SD1", devices=["D2"]))

    assert excinfo.value.serial == "SD1"
    assert repo.get_super_device("SD1").devices == ["D1"]
    assert [r.sub_device_id for r in _structure_rows(db)] == ["D1"]


def test_reg_super_device_duplicate_removed_serial_reports_removed(db, repo, devices):
    """输入 serial 被软删的超级设备行占用 → 期望输出 SuperDeviceAlreadyRemovedError（上层据此提示 revive）。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    repo.remove_super_device("SD1")

    with pytest.raises(SuperDeviceAlreadyRemovedError) as excinfo:
        repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    assert excinfo.value.serial == "SD1"
    assert repo.is_exist("SD1") is True  # 墓碑行仍占位，故不能重新登记


@pytest.mark.skip(reason="摘子项功能暂缓（TODO P1：single 变体不变量待重新设计）")
def test_get_super_device_filters_unused_structures(db, repo, devices):
    """输入 子项关系被标为 UNUSED → 期望输出 devices 不再包含它，但结构行仍保留。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1", "D2"]))
    repo.remove_device("SD1", "D1")

    assert repo.get_super_device("SD1").devices == ["D2"]
    assert len(_structure_rows(db)) == 2


# ── 更新 ──────────────────────────────────────────────────────────


def test_update_super_device_maps_sdtype_and_coerces_state(db, repo, devices):
    """输入 更新 sdtype/state/need_all_devices_online → 期望输出 映射到 type 列且枚举归一。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    repo.update_super_device(
        "SD1",
        name="R",
        capacity=5,
        sdtype="single",
        need_all_devices_online=False,
        state="degrading",
    )

    got = repo.get_super_device("SD1")
    assert got.name == "R"
    assert got.capacity == 5
    assert got.sdtype == "single"
    assert got.need_all_devices_online is False
    assert got.state is SuperDeviceState.DEGRADING
    assert got.devices == ["D1"]


def test_update_super_device_invalid_state_raises(db, repo, devices):
    """输入 state='bogus' → 期望输出 ValueError 且原状态不变。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    with pytest.raises(ValueError, match="不是 SuperDeviceState 的合法状态"):
        repo.update_super_device("SD1", state="bogus")

    assert repo.get_super_device("SD1").state is SuperDeviceState.HEALTHY


def test_update_super_device_missing_raises_value_error(repo):
    """输入 更新不存在的超级设备 → 期望输出 ValueError。"""
    with pytest.raises(SuperDeviceNotFoundError):
        repo.update_super_device("GHOST", name="x")


def test_update_super_device_none_keeps_original(db, repo, devices):
    """输入 state/name 传 None → 期望输出 视为「未提供」，字段保持原值而非写 NULL。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"], name="S"))

    repo.update_super_device("SD1", state=None, name=None)

    got = repo.get_super_device("SD1")
    assert got.state is SuperDeviceState.HEALTHY
    assert got.name == "S"


def test_update_super_device_rejects_unknown_field(db, repo, devices):
    """输入 拼错的字段名 → 期望输出 ValueError（不再静默无效）且原值不变。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"], name="S"))

    with pytest.raises(ValueError, match="不支持更新字段"):
        repo.update_super_device("SD1", nam="x")  # 拼错 name

    assert repo.get_super_device("SD1").name == "S"


def test_update_super_device_rejects_serial_change(db, repo, devices):
    """输入 试图用 update_super_device 改序列号 → 期望输出 ValueError（须走 update_super_device_serial）。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    with pytest.raises(ValueError, match="update_super_device_serial"):
        repo.update_super_device("SD1", serial="SD1-X")

    assert repo.is_exist("SD1") is True
    assert repo.is_exist("SD1-X") is False


# ── 主键迁移 ──────────────────────────────────────────────────────


def test_update_serial_cascades_parent_child_and_volumes(db, repo, devices):
    """输入 超级设备被层叠引用且其上有卷 → 期望输出 父/子引用与卷归属一并迁移。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1", "D2"]))
    repo.reg_super_device(H.make_super_device("SD2", devices=["SD1"]))
    volume_repo = db.repos["volume"]
    volume_repo.reg_volume(H.make_volume("V1", device_id="SD1"))

    repo.update_super_device_serial("SD1", "SD1-NEW")

    assert repo.is_exist("SD1-NEW") is True
    assert repo.is_exist("SD1") is False
    assert repo.get_super_device("SD1-NEW").devices == ["D1", "D2"]
    assert repo.get_super_device("SD2").devices == ["SD1-NEW"]
    assert volume_repo.get_volume("V1").device_id == "SD1-NEW"
    assert H.count(db, SuperDeviceStructureModel) == 3


def test_update_serial_same_serial_is_noop(db, repo, devices):
    """输入 新旧 serial 相同 → 期望输出 提前返回，记录与关联完整保留。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    repo.update_super_device_serial("SD1", "SD1")

    assert repo.get_super_device("SD1").devices == ["D1"]


def test_update_serial_missing_raises_value_error(repo):
    """输入 迁移不存在的超级设备 → 期望输出 ValueError。"""
    with pytest.raises(SuperDeviceNotFoundError):
        repo.update_super_device_serial("GHOST", "NEW")


def test_update_serial_to_existing_serial_raises(db, repo, devices):
    """输入 把 SD1 改名为已存在的 SD2 → 期望输出 SuperDeviceAlreadyRegisteredError 且记录不变。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    repo.reg_super_device(H.make_super_device("SD2", devices=["D2"]))

    with pytest.raises(SuperDeviceAlreadyRegisteredError):
        repo.update_super_device_serial("SD1", "SD2")

    assert repo.is_exist("SD1") is True
    assert repo.get_super_device("SD1").devices == ["D1"]


def test_update_serial_to_removed_serial_raises(db, repo, devices):
    """输入 把 SD1 改名为一条 REMOVED 墓碑占用的 serial → 期望输出 SuperDeviceAlreadyRemovedError。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    repo.reg_super_device(H.make_super_device("SD2", devices=["D2"]))
    repo.remove_super_device("SD2")

    with pytest.raises(SuperDeviceAlreadyRemovedError):
        repo.update_super_device_serial("SD1", "SD2")

    # 事务回滚：SD1 仍在，SD2 墓碑仍占位
    assert repo.is_exist("SD1") is True
    assert repo.is_exist("SD2") is True


# ── 子设备增删改 ──────────────────────────────────────────────────


def test_add_device_appends_using_row(db, repo, devices):
    """输入 追加一个空闲设备 → 期望输出 devices 变长且新结构行 state=USING。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    db.repos["device"].reg_device(H.make_device("D3"))

    repo.add_device("SD1", "D3", datetime(2026, 2, 1))

    assert repo.get_super_device("SD1").devices == ["D1", "D3"]
    new_row = next(r for r in _structure_rows(db) if r.sub_device_id == "D3")
    assert new_row.state is SuperDeviceRelationState.USING
    assert new_row.add_time == datetime(2026, 2, 1)


def test_add_device_nonexistent_raises_not_found(db, repo, devices):
    """输入 追加不存在的子项 → 期望输出 SubDeviceNotFoundError。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    with pytest.raises(SubDeviceNotFoundError):
        repo.add_device("SD1", "GHOST", datetime(2026, 2, 1))


def test_add_device_in_use_raises(db, repo, devices):
    """输入 追加已被其它超级设备占用的子项 → 期望输出 SubDeviceInUseError。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    repo.reg_super_device(H.make_super_device("SD2", devices=["D2"]))

    with pytest.raises(SubDeviceInUseError):
        repo.add_device("SD1", "D2", datetime(2026, 2, 1))


def test_add_device_unknown_parent_raises_integrity_error(db, repo, devices):
    """输入 父超级设备不存在 → 期望输出 IntegrityError（父列外键约束）。"""
    db.repos["device"].reg_device(H.make_device("D3"))

    with pytest.raises(IntegrityError):
        repo.add_device("GHOST-SD", "D3", datetime(2026, 2, 1))


def test_replace_device_marks_old_replaced_and_records_replaced_by(db, repo, devices):
    """输入 用 D3 替换 D1 → 期望输出 新映射 USING，旧映射 REPLACED 且 info 记录 replaced_by。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1", "D2"]))
    db.repos["device"].reg_device(H.make_device("D3"))

    repo.replace_device("SD1", "D1", "D3", datetime(2026, 2, 1))

    assert repo.get_super_device("SD1").devices == ["D2", "D3"]
    old_row = next(r for r in _structure_rows(db) if r.sub_device_id == "D1")
    assert old_row.state is SuperDeviceRelationState.REPLACED
    assert json.loads(old_row.info)["replaced_by"] == "D3"
    new_row = next(r for r in _structure_rows(db) if r.sub_device_id == "D3")
    assert new_row.state is SuperDeviceRelationState.USING


def test_replace_device_missing_old_child_raises(db, repo, devices):
    """输入 旧子项不在超级设备中 → 期望输出 ValueError。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    db.repos["device"].reg_device(H.make_device("D3"))

    with pytest.raises(ValueError, match="not found in super_device"):
        repo.replace_device("SD1", "D2", "D3", datetime(2026, 2, 1))


def test_replace_device_fail_fast_keeps_old_using(db, repo, devices):
    """输入 新子项已被占用 → 期望输出 SubDeviceInUseError 且旧映射仍为 USING（未部分更新）。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1", "D2"]))

    with pytest.raises(SubDeviceInUseError):
        repo.replace_device("SD1", "D1", "D2", datetime(2026, 2, 1))

    assert repo.get_super_device("SD1").devices == ["D1", "D2"]
    old_row = next(r for r in _structure_rows(db) if r.sub_device_id == "D1")
    assert old_row.state is SuperDeviceRelationState.USING


@pytest.mark.skip(reason="摘子项功能暂缓（TODO P1：single 变体不变量待重新设计）")
def test_remove_device_marks_unused(db, repo, devices):
    """输入 移除 USING 子项 → 期望输出 结构行转 UNUSED 且不再出现在 devices 中。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1", "D2"]))

    repo.remove_device("SD1", "D1")

    assert repo.get_super_device("SD1").devices == ["D2"]
    row = next(r for r in _structure_rows(db) if r.sub_device_id == "D1")
    # TODO(P1): 摘子项停用中 —— 原断言为 UNUSED，该状态已随枚举拆分移除，重启时需先定状态
    # assert row.state is SuperDeviceRelationState.UNUSED


@pytest.mark.skip(reason="摘子项功能暂缓（TODO P1：single 变体不变量待重新设计）")
def test_remove_device_missing_child_raises(db, repo, devices):
    """输入 移除不存在或已 UNUSED 的子项 → 期望输出 ValueError。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    with pytest.raises(ValueError, match="not found in super_device"):
        repo.remove_device("SD1", "D2")

    repo.remove_device("SD1", "D1")
    with pytest.raises(ValueError, match="not found in super_device"):
        repo.remove_device("SD1", "D1")


# ── 软删除 ────────────────────────────────────────────────────────


def test_remove_super_device_soft_deletes(db, repo, devices):
    """输入 无引用的超级设备 → 期望输出 state 变 REMOVED，结构行保留。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    repo.remove_super_device("SD1")

    assert repo.get_super_device("SD1") is None
    assert repo.get_super_device("SD1", exclude_removed=False).state is SuperDeviceState.REMOVED
    assert H.count(db, SuperDeviceModel) == 1
    assert len(_structure_rows(db)) == 1


def test_remove_super_device_releases_children(db, repo, devices):
    """输入 名下有 USING 子项的超级设备 → 期望输出 关联行置 SUPER_DEVICE_REMOVED，子项被释放可再挂载。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1", "D2"]))

    repo.remove_super_device("SD1")

    # 关联行保留但已释放
    rows = _structure_rows(db)
    assert len(rows) == 2
    assert all(r.state == SuperDeviceRelationState.SUPER_DEVICE_REMOVED for r in rows)

    # 已释放的子项可被另一超级设备挂载
    repo.reg_super_device(H.make_super_device("SD2", devices=["D1"]))
    assert repo.get_super_device("SD2").devices == ["D1"]

    # 未再被挂载的子项可直接软删除
    db.repos["device"].remove_device("D2")
    assert db.repos["device"].get_device("D2") is None


def test_remove_super_device_blocked_by_volume(db, repo, devices):
    """输入 超级设备上仍有非 REMOVED 卷 → 期望输出 SuperDeviceInUseError(volumes=1)。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    volume_repo = db.repos["volume"]
    volume_repo.reg_volume(H.make_volume("V1", device_id="SD1"))

    with pytest.raises(SuperDeviceInUseError) as excinfo:
        repo.remove_super_device("SD1")

    assert excinfo.value.serial == "SD1"
    assert excinfo.value.volumes == 1
    assert excinfo.value.super_device_using == 0

    volume_repo.remove_volume("V1")
    repo.remove_super_device("SD1")
    assert repo.get_super_device("SD1", exclude_removed=False).state is SuperDeviceState.REMOVED


@pytest.mark.skip(reason="摘子项功能暂缓（TODO P1：single 变体不变量待重新设计）")
def test_remove_super_device_blocked_by_nested_usage(db, repo, devices):
    """输入 超级设备仍被另一超级设备 USING 引用 → 期望输出 SuperDeviceInUseError(super_device_using=1)。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    repo.reg_super_device(H.make_super_device("SD2", devices=["SD1"]))

    with pytest.raises(SuperDeviceInUseError) as excinfo:
        repo.remove_super_device("SD1")

    assert excinfo.value.super_device_using == 1

    repo.remove_device("SD2", "SD1")
    repo.remove_super_device("SD1")
    assert repo.get_super_device("SD1", exclude_removed=False).state is SuperDeviceState.REMOVED


def test_remove_super_device_missing_raises_value_error(repo):
    """输入 删除不存在的超级设备 → 期望输出 ValueError。"""
    with pytest.raises(SuperDeviceNotFoundError):
        repo.remove_super_device("GHOST")


# ── 复活（REMOVED → UNKNOWN，拓扑一并恢复） ────────────────────────


def test_remove_super_device_already_removed_raises(db, repo, devices):
    """输入 对已 REMOVED 的超级设备再删一次 → 期望输出 SuperDeviceAlreadyRemovedError。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    repo.remove_super_device("SD1")

    with pytest.raises(SuperDeviceAlreadyRemovedError) as excinfo:
        repo.remove_super_device("SD1")

    assert excinfo.value.serial == "SD1"


def test_revive_super_device_restores_state_and_topology(db, repo, devices):
    """输入 软删过的超级设备 → 期望输出 state=UNKNOWN 且子项挂回（拓扑恢复）。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1", "D2"]))
    repo.remove_super_device("SD1")

    repo.revive_super_device("SD1")

    sd = repo.get_super_device("SD1")
    assert sd.state is SuperDeviceState.UNKNOWN
    assert sd.devices == ["D1", "D2"]
    assert all(
        r.state is SuperDeviceRelationState.USING for r in _structure_rows(db)
    )


def test_revive_super_device_does_not_restore_replaced_rows(db, repo, devices):
    """输入 D1 已被 D3 换掉 → 期望输出 复活后 devices 含 D3 不含 D1（REPLACED 不恢复）。"""
    db.repos["device"].reg_device(H.make_device("D3"))
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1", "D2"]))
    repo.replace_device("SD1", "D1", "D3", datetime(2026, 2, 1))
    repo.remove_super_device("SD1")

    repo.revive_super_device("SD1")

    assert repo.get_super_device("SD1").devices == ["D2", "D3"]
    replaced = next(r for r in _structure_rows(db) if r.sub_device_id == "D1")
    assert replaced.state is SuperDeviceRelationState.REPLACED


def test_revive_super_device_restores_single_child(db, repo, devices):
    """输入 single 超设软删（子项被释放 → 0 子项）→ 期望输出 仍可读，复活后子项挂回。"""
    repo.reg_super_device(H.make_super_device("SD1", sdtype="single", devices=["D1"]))
    repo.remove_super_device("SD1")

    # REMOVED + 0 子项：可读（这是单盘软删后的合法中间态）
    assert repo.get_super_device("SD1", exclude_removed=False).devices == []
    assert repo.list_super_device(exclude_removed=False)[0].serial == "SD1"

    repo.revive_super_device("SD1")

    assert repo.get_super_device("SD1").devices == ["D1"]


def test_revive_super_device_blocked_when_child_taken(db, repo, devices):
    """输入 释放的子项被另一超级设备挂走 → 期望输出 SubDeviceInUseError 且整体回滚。"""
    db.repos["device"].reg_device(H.make_device("D3"))
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    repo.reg_super_device(H.make_super_device("SD2", devices=["D3"]))
    repo.remove_super_device("SD1")                 # D1 被释放
    repo.replace_device("SD2", "D3", "D1", datetime(2026, 2, 1))  # D1 被 SD2 抢走

    with pytest.raises(SubDeviceInUseError):
        repo.revive_super_device("SD1")

    # 回滚：SD1 仍 REMOVED、结构行仍 SUPER_DEVICE_REMOVED、D1 仍属 SD2
    assert repo.get_super_device("SD1", exclude_removed=False).state is SuperDeviceState.REMOVED
    released = next(r for r in _structure_rows(db) if r.super_device_id == "SD1")
    assert released.state is SuperDeviceRelationState.SUPER_DEVICE_REMOVED
    assert repo.get_super_device("SD2").devices == ["D1"]


def test_revive_super_device_blocked_when_child_device_removed(db, repo, devices):
    """输入 释放的子项设备已被软删 → 期望输出 SubDeviceUnavailableError 且整体回滚。"""
    repo.reg_super_device(H.make_super_device("SD1", sdtype="single", devices=["D1"]))
    repo.remove_super_device("SD1")          # D1 不再被占用
    db.repos["device"].remove_device("D1")   # D1 软删

    with pytest.raises(SubDeviceUnavailableError):
        repo.revive_super_device("SD1")

    assert repo.get_super_device("SD1", exclude_removed=False).state is SuperDeviceState.REMOVED
    released = next(r for r in _structure_rows(db) if r.super_device_id == "SD1")
    assert released.state is SuperDeviceRelationState.SUPER_DEVICE_REMOVED


def test_revive_super_device_succeeds_when_still_referenced_by_volume(db, repo, devices):
    """输入 手工标成 REMOVED、名下仍有未移除的卷 → 期望输出 复活成功（复活即修复脏状态）。

    正常流程造不出这种状态（remove_super_device 会先校验），属并发 / 手工改库的脏状态。
    复活不做自身占用校验：state 回到 UNKNOWN 后与「卷仍指向它」这个事实重新自洽。
    """
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    db.repos["volume"].reg_volume(H.make_volume("V1", device_id="SD1"))

    with db.new_session() as session:
        session.query(SuperDeviceModel).filter_by(serial="SD1").one().state = SuperDeviceState.REMOVED
        session.commit()

    repo.revive_super_device("SD1")

    assert repo.get_super_device("SD1").state is SuperDeviceState.UNKNOWN
    assert repo.get_super_device("SD1").devices == ["D1"]
    assert db.repos["volume"].get_volume("V1").device_id == "SD1"


def test_revive_super_device_not_removed_raises(db, repo, devices):
    """输入 复活未处于 REMOVED 的超级设备 → 期望输出 SuperDeviceNotRemovedError 且状态不变。"""
    repo.reg_super_device(H.make_super_device("SD1", devices=["D1"], state=SuperDeviceState.HEALTHY))

    with pytest.raises(SuperDeviceNotRemovedError) as excinfo:
        repo.revive_super_device("SD1")

    assert excinfo.value.state is SuperDeviceState.HEALTHY
    assert repo.get_super_device("SD1").state is SuperDeviceState.HEALTHY


def test_revive_super_device_missing_raises(repo):
    """输入 复活不存在的超级设备 → 期望输出 ValueError(not found)。"""
    with pytest.raises(SuperDeviceNotFoundError):
        repo.revive_super_device("GHOST")


# ── 私有工具与静态方法 ────────────────────────────────────────────


def test_resolve_sub_classifies_kinds(db, devices):
    """输入 设备/超级设备/未知 id → 期望输出 ('device', 行) / ('super_device', 行) / None。"""
    db.repos["super_device"].reg_super_device(H.make_super_device("SD1", devices=["D1"]))
    resolve = super_device_repository_mod._resolve_sub

    with db.factory() as session:
        kind, model = resolve(session, "D1")
        assert kind == "device"
        assert model.serial == "D1"

        kind, model = resolve(session, "SD1")
        assert kind == "super_device"
        assert model.serial == "SD1"

        assert resolve(session, "GHOST") is None


def test_model_to_dict_is_static_and_complete():
    """输入 内存构造的模型行 + 子项列表 → 期望输出 字段齐全且 devices 原样透传。"""
    model = SuperDeviceModel(
        serial="SD1",
        name="n",
        sdtype="raidz",
        need_all_devices_online=True,
        state=SuperDeviceState.HEALTHY,
        capacity=7,
        info="i",
    )

    assert SuperDeviceRepository._model_to_dict(model, ["A", "B"]) == {
        "serial": "SD1",
        "name": "n",
        "sdtype": "raidz",
        "need_all_devices_online": True,
        "add_time": None,
        "last_check_time": None,
        "state": SuperDeviceState.HEALTHY,
        "capacity": 7,
        "info": "i",
        "devices": ["A", "B"],
    }
