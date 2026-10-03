# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/storage/super_volume_repository.py —— SuperVolumeRepository 隔离单测。

目的（测什么）：
- 注册/查询/列表/`is_exist`，以及超级卷与子卷关联行（USING 过滤）的读写；
- `reg_super_volume` 的主行 + 关联行同事务写入，未知/不可用/被占用的子卷抛领域异常并整体回滚；
  改成已存在 / 已移除的 serial → 抛领域异常（AlreadyRegistered / AlreadyRemoved）；
  name 无唯一约束 → 同名（含与 REMOVED 行同名）可正常登记；
- `add_volume`：子卷已属于其它超级卷 → SubVolumeInUseError；已有退役行（REPLACED）→ 撞唯一约束；
- `replace_volume`：旧卷转 REPLACED 并记 replaced_by，新卷转 USING；新卷不可挂载时 fail-fast；
- `remove_super_volume`：自身 REMOVED 且 USING 关联转 SUPER_VOLUME_REMOVED；
- `revive_super_volume`：REMOVED → UNKNOWN，恢复 SUPER_VOLUME_REMOVED 拓扑，校验子卷可用；
- `update_super_volume` 的 svtype→type 映射、state 归一化、None 保持原值、拒绝未知字段 / 改 serial / 置 REMOVED；
  `update_super_volume_serial` 的关联迁移、同值早退与目标 serial 冲突预检；
- `get_super_volume` / `list_super_volume` 默认排除 REMOVED；
- 静态 `_model_to_dict`。

输入：`tmp_path` 下每个用例独占的临时 SQLite 库 + `_helpers` 构造的领域对象。

期望输出：查询结果、关联行状态与异常类型符合仓储 docstring。
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from domain.storage.super_volume.enum import SuperVolumeRelationState
from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.super_volume.errors import (
    SubVolumeInUseError,
    SubVolumeNotFoundError,
    SubVolumeUnavailableError,
    SuperVolumeAlreadyRegisteredError,
    SuperVolumeAlreadyRemovedError,
    SuperVolumeNotFoundError,
    SuperVolumeNotRemovedError,
)
from domain.storage.super_volume.repo import SuperVolumeRepositoryABC
# TODO(P1): 批量 add_volumes 停用中 —— SuperVolumeStructure 仅其使用，恢复时一并取消注释
# from domain.storage.super_volume.structure import SuperVolumeStructure
from infra.persistence.models import SuperVolumeModel, SuperVolumeStructureModel
from infra.persistence.storage.super_volume_repository import SuperVolumeRepository
from tests.unit_test.infra.persistence import _helpers as H


@pytest.fixture
def db(tmp_path):
    """每个用例独占的临时 SQLite 库（仅建表）。"""
    handle = H.new_db(tmp_path / "super_volume.db")
    yield handle
    handle.dispose()


@pytest.fixture
def repo(db):
    """绑定该库的 SuperVolumeRepository。"""
    return db.repos["super_volume"]


@pytest.fixture
def volumes(db):
    """登记三个卷 V1 / V2 / V3（关联行的外键要求卷真实存在）。"""
    H.seed_volumes(db, ("V1", "V2", "V3"))
    return ("V1", "V2", "V3")


def _structure_rows(db) -> list[SuperVolumeStructureModel]:
    """读取全部超级卷-卷关联行。"""
    return H.query_all(db, SuperVolumeStructureModel)


# ── 构造与注册 ────────────────────────────────────────────────────


def test_repository_is_abc_implementation(db, repo):
    """输入 新建仓储 → 期望输出 是 SuperVolumeRepositoryABC 实例且复用同一会话工厂。"""
    assert isinstance(repo, SuperVolumeRepositoryABC)
    assert repo.session_factory is db.factory


def test_reg_and_get_super_volume(db, repo, volumes):
    """输入 copy 型超级卷含两个子卷 → 期望输出 字段往返且 volumes 与登记顺序一致。"""
    repo.reg_super_volume(
        H.make_super_volume("SV1", svtype="copy", method="copy", volumes=["V1", "V2"])
    )

    got = repo.get_super_volume("SV1")

    assert isinstance(got, SuperVolume)
    assert got.serial == "SV1"
    assert got.name == "SV1"
    assert got.svtype == "copy"
    assert got.method == "copy"
    assert got.state is SuperVolumeState.HEALTHY
    assert got.add_time == H.FIXED_TIME
    assert got.volumes == ["V1", "V2"]
    assert repo.is_exist("SV1") is True
    assert repo.is_exist(got) is True
    assert repo.is_exist("GHOST") is False


def test_reg_super_volume_none_state_falls_back_to_column_default(db, repo, volumes):
    """输入 state=None → 期望输出 落库为列默认 HEALTHY（不留 NULL）。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"], state=None))

    assert repo.get_super_volume("SV1").state is SuperVolumeState.HEALTHY


def test_reg_super_volume_without_volumes(db, repo):
    """输入 空子卷列表 → 期望输出 主行落库且关联行数为 0。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=[]))

    assert repo.get_super_volume("SV1").volumes == []
    assert _structure_rows(db) == []


def test_reg_super_volume_unknown_volume_rolls_back(db, repo, volumes):
    """输入 子卷不存在 → 期望输出 SubVolumeNotFoundError 且主行也回滚。"""
    with pytest.raises(SubVolumeNotFoundError):
        repo.reg_super_volume(H.make_super_volume("SV1", volumes=["GHOST"]))

    assert repo.is_exist("SV1") is False
    assert _structure_rows(db) == []


def test_reg_super_volume_rejects_removed_child(db, repo, volumes):
    """输入 子卷已 REMOVED → 期望输出 SubVolumeUnavailableError 且整体回滚。"""
    db.repos["volume"].remove_volume("V1")

    with pytest.raises(SubVolumeUnavailableError):
        repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    assert repo.is_exist("SV1") is False
    assert _structure_rows(db) == []


def test_reg_super_volume_rejects_in_use_child(db, repo, volumes):
    """输入 子卷已属其它超级卷（USING）→ 期望输出 SubVolumeInUseError 且整体回滚。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    with pytest.raises(SubVolumeInUseError):
        repo.reg_super_volume(H.make_super_volume("SV2", volumes=["V1"]))

    assert repo.is_exist("SV2") is False
    assert H.count(db, SuperVolumeStructureModel) == 1


def test_reg_super_volume_duplicate_serial_raises_already_registered(db, repo, volumes):
    """输入 登记已存在的 serial（非 REMOVED）→ 期望输出 SuperVolumeAlreadyRegisteredError。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    with pytest.raises(SuperVolumeAlreadyRegisteredError) as excinfo:
        repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V2"]))

    assert excinfo.value.serial == "SV1"
    assert excinfo.value.state is SuperVolumeState.HEALTHY
    assert H.count(db, SuperVolumeModel) == 1


def test_reg_super_volume_duplicate_removed_serial_reports_removed(db, repo, volumes):
    """输入 serial 已被软删行占位 → 期望输出 SuperVolumeAlreadyRemovedError（上层据此提示 revive）。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.remove_super_volume("SV1")

    with pytest.raises(SuperVolumeAlreadyRemovedError):
        repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V2"]))

    assert H.count(db, SuperVolumeModel) == 1


def test_reg_super_volume_duplicate_name_allowed(db, repo, volumes):
    """输入 名称与已有超级卷重复（serial 不同）→ 期望输出 两行都正常落库。

    name 已去掉唯一约束（2026-10-02）：名字只是标签，查重靠 serial。
    """
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.reg_super_volume(H.make_super_volume("SV2", name="SV1", volumes=["V2"]))

    assert repo.is_exist("SV1") is True
    assert repo.is_exist("SV2") is True
    assert H.count(db, SuperVolumeModel) == 2


def test_reg_super_volume_reuses_name_after_removed(db, repo, volumes):
    """输入 与已软删除（REMOVED）超级卷同名的超级卷 → 期望输出 可正常登记。

    这是去掉 name 唯一约束的直接动机：旧行还在库里，但不应该继续霸占名字。
    """
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.remove_super_volume("SV1")

    repo.reg_super_volume(H.make_super_volume("SV2", name="SV1", volumes=["V2"]))

    assert repo.is_exist("SV2") is True
    assert H.count(db, SuperVolumeModel) == 2


def test_get_super_volume_missing_returns_none(repo):
    """输入 不存在的 serial → 期望输出 None。"""
    assert repo.get_super_volume("GHOST") is None


def test_list_super_volume_returns_all(db, repo, volumes):
    """输入 空库/登记两个超级卷 → 期望输出 [] / 两个对象。"""
    assert repo.list_super_volume() == []

    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.reg_super_volume(H.make_super_volume("SV2", volumes=["V2"]))

    assert sorted(s.serial for s in repo.list_super_volume()) == ["SV1", "SV2"]


def test_get_and_list_exclude_removed_by_default(db, repo, volumes):
    """输入 已软删除的超级卷 → 期望输出 默认视为不存在；exclude_removed=False 时返回 REMOVED。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.remove_super_volume("SV1")

    assert repo.get_super_volume("SV1") is None
    assert repo.get_super_volume("SV1", exclude_removed=False).state is SuperVolumeState.REMOVED
    assert repo.list_super_volume() == []
    assert [s.serial for s in repo.list_super_volume(exclude_removed=False)] == ["SV1"]


def test_list_super_volume_includes_default_placeholder(tmp_path):
    """输入 已填充默认数据的库 → 期望输出 列表含 EXTERNAL_SUPERVOLUME 且子卷为默认卷。"""
    handle = H.new_db(tmp_path / "seeded.db", with_defaults=True)
    try:
        items = handle.repos["super_volume"].list_super_volume()
        assert [s.serial for s in items] == ["EXTERNAL_SUPERVOLUME"]
        assert items[0].volumes == ["EXTERNAL_VOLUME"]
    finally:
        handle.dispose()


# ── 更新 ──────────────────────────────────────────────────────────


def test_update_super_volume_maps_svtype_and_coerces_state(db, repo, volumes):
    """输入 更新 svtype/state/method → 期望输出 svtype 映射到 type 列且 state 归一为枚举。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    repo.update_super_volume(
        "SV1", name="copies", method="copy", svtype="pair", state="DANGER"
    )

    got = repo.get_super_volume("SV1")
    assert got.name == "copies"
    assert got.method == "copy"
    assert got.svtype == "pair"
    assert got.state is SuperVolumeState.DANGER
    assert got.volumes == ["V1"]


def test_update_super_volume_invalid_state_raises(db, repo, volumes):
    """输入 state='bogus' → 期望输出 ValueError 且原状态不变。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    with pytest.raises(ValueError, match="不是 SuperVolumeState 的合法状态"):
        repo.update_super_volume("SV1", state="bogus")

    assert repo.get_super_volume("SV1").state is SuperVolumeState.HEALTHY


def test_update_super_volume_missing_raises_value_error(repo):
    """输入 更新不存在的超级卷 → 期望输出 ValueError。"""
    with pytest.raises(SuperVolumeNotFoundError):
        repo.update_super_volume("GHOST", name="x")


def test_update_super_volume_none_keeps_original(db, repo, volumes):
    """输入 state/name 传 None → 期望输出 视为「未提供」，字段保持原值而非写 NULL。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"], name="S"))

    repo.update_super_volume("SV1", state=None, name=None)

    got = repo.get_super_volume("SV1")
    assert got.state is SuperVolumeState.HEALTHY
    assert got.name == "S"


def test_update_super_volume_rejects_removed_state(db, repo, volumes):
    """输入 state='REMOVED' → 期望输出 ValueError 且原状态不变（软删除必须走 remove_super_volume）。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"], state=SuperVolumeState.HEALTHY))

    with pytest.raises(ValueError, match="REMOVED"):
        repo.update_super_volume("SV1", state="REMOVED")

    assert repo.get_super_volume("SV1").state is SuperVolumeState.HEALTHY


def test_update_super_volume_rejects_unknown_field(db, repo, volumes):
    """输入 拼错的字段名 → 期望输出 ValueError（不再静默无效）且原值不变。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"], name="S"))

    with pytest.raises(ValueError, match="不支持更新字段"):
        repo.update_super_volume("SV1", nam="x")  # 拼错 name

    assert repo.get_super_volume("SV1").name == "S"


def test_update_super_volume_rejects_serial_change(db, repo, volumes):
    """输入 试图用 update_super_volume 改序列号 → 期望输出 ValueError 且 serial 不变。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    with pytest.raises(ValueError, match="update_super_volume_serial"):
        repo.update_super_volume("SV1", serial="SV1-X")

    assert repo.is_exist("SV1") is True
    assert repo.is_exist("SV1-X") is False


# ── add_volume ────────────────────────────────────────────────────


def test_add_volume_appends_member(db, repo, volumes):
    """输入 单个追加子卷 → 期望输出 volumes 增加且关联行 state=USING。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    repo.add_volume("SV1", "V2", datetime.now())

    assert repo.get_super_volume("SV1").volumes == ["V1", "V2"]
    row = next(r for r in _structure_rows(db) if r.volume_id == "V2")
    assert row.state is SuperVolumeRelationState.USING


def test_add_volume_rejects_volume_owned_by_another_super_volume(db, repo, volumes):
    """输入 子卷已属于其它超级卷 → 期望输出 SubVolumeInUseError 且不新增行。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.reg_super_volume(H.make_super_volume("SV2", volumes=["V2"]))

    with pytest.raises(SubVolumeInUseError):
        repo.add_volume("SV1", "V2", datetime.now())

    assert H.count(db, SuperVolumeStructureModel) == 2


def test_add_volume_rejects_existing_replaced_membership(db, repo, volumes):
    """输入 子卷在关联表中已有 REPLACED 行 → 期望输出 IntegrityError（volume_id 唯一约束）。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.replace_volume("SV1", "V1", "V3", datetime.now())

    with pytest.raises(IntegrityError):
        repo.add_volume("SV1", "V1", datetime.now())


# ── replace_volume ────────────────────────────────────────────────


def test_replace_volume_marks_replaced_and_records_replaced_by(db, repo, volumes):
    """输入 存在的 USING 成员 → 期望输出 旧卷转 REPLACED 并记 replaced_by，新卷转 USING。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1", "V2"]))

    repo.replace_volume("SV1", "V1", "V3", datetime.now())

    assert repo.get_super_volume("SV1").volumes == ["V2", "V3"]
    old = next(r for r in _structure_rows(db) if r.volume_id == "V1")
    assert old.state is SuperVolumeRelationState.REPLACED
    assert "replaced_by" in old.info and "V3" in old.info
    new = next(r for r in _structure_rows(db) if r.volume_id == "V3")
    assert new.state is SuperVolumeRelationState.USING


def test_replace_volume_missing_old_raises(db, repo, volumes):
    """输入 旧卷不是该超级卷的 USING 成员 → 期望输出 ValueError 且不改动。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    with pytest.raises(ValueError, match="not found in super_volume"):
        repo.replace_volume("SV1", "V2", "V3", datetime.now())

    assert repo.get_super_volume("SV1").volumes == ["V1"]


def test_replace_volume_rejects_unavailable_new(db, repo, volumes):
    """输入 新卷已被其它超级卷 USING 占用 → 期望输出 SubVolumeInUseError（fail-fast）。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.reg_super_volume(H.make_super_volume("SV2", volumes=["V2"]))

    with pytest.raises(SubVolumeInUseError):
        repo.replace_volume("SV1", "V1", "V2", datetime.now())


# ── remove_volumes（摘子卷功能暂缓） ───────────────────────────────


@pytest.mark.skip(reason="摘子卷功能暂缓（TODO P1：阵列迁移未实现，且 volume_id 硬唯一约束阻塞复用）")
def test_remove_volumes_releases_members(db, repo, volumes):
    """输入 移除 USING 成员 → 期望输出 关联行转 REPLACED 且不再计入成员视图。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1", "V2"]))

    repo.remove_volumes("SV1", ["V1"])

    assert repo.get_super_volume("SV1").volumes == ["V2"]
    row = next(r for r in _structure_rows(db) if r.volume_id == "V1")
    assert row.state is SuperVolumeRelationState.REPLACED


@pytest.mark.skip(reason="摘子卷功能暂缓（TODO P1：阵列迁移未实现，且 volume_id 硬唯一约束阻塞复用）")
def test_remove_volumes_partial_failure_does_not_update_anything(db, repo, volumes):
    """输入 待移除列表含非 USING 成员 → 期望输出 ValueError 且其余成员保持 USING（不半更新）。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1", "V2"]))

    with pytest.raises(ValueError, match="不是"):
        repo.remove_volumes("SV1", ["V1", "GHOST"])

    assert repo.get_super_volume("SV1").volumes == ["V1", "V2"]


@pytest.mark.skip(reason="摘子卷功能暂缓（TODO P1：阵列迁移未实现，且 volume_id 硬唯一约束阻塞复用）")
def test_remove_volumes_missing_parent_raises(db, repo, volumes):
    """输入 父超级卷不存在 → 期望输出 SuperVolumeNotFoundError。"""
    with pytest.raises(SuperVolumeNotFoundError):
        repo.remove_volumes("GHOST", ["V1"])


@pytest.mark.skip(reason="摘子卷功能暂缓（TODO P1：阵列迁移未实现，且 volume_id 硬唯一约束阻塞复用）")
def test_remove_volumes_rejects_already_replaced_member(db, repo, volumes):
    """输入 重复移除同一成员 → 期望输出 第二次 ValueError（已非 USING）。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.remove_volumes("SV1", ["V1"])

    with pytest.raises(ValueError, match="不是"):
        repo.remove_volumes("SV1", ["V1"])


# ── 软删除 ────────────────────────────────────────────────────────


def test_remove_super_volume_marks_removed_and_releases_members(db, repo, volumes):
    """输入 无外键冲突的超级卷 → 期望输出 自身 REMOVED、全部 USING 关联转 SUPER_VOLUME_REMOVED。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1", "V2"]))

    repo.remove_super_volume("SV1")

    assert (
        repo.get_super_volume("SV1", exclude_removed=False).state
        is SuperVolumeState.REMOVED
    )
    rows = _structure_rows(db)
    assert len(rows) == 2
    assert {r.state for r in rows} == {SuperVolumeRelationState.SUPER_VOLUME_REMOVED}
    assert repo.get_super_volume("SV1", exclude_removed=False).volumes == []


def test_remove_super_volume_missing_raises_value_error(repo):
    """输入 删除不存在的超级卷 → 期望输出 ValueError。"""
    with pytest.raises(SuperVolumeNotFoundError):
        repo.remove_super_volume("GHOST")


def test_remove_super_volume_already_removed_raises(db, repo, volumes):
    """输入 对已 REMOVED 的超级卷再删一次 → 期望输出 SuperVolumeAlreadyRemovedError。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.remove_super_volume("SV1")

    with pytest.raises(SuperVolumeAlreadyRemovedError) as excinfo:
        repo.remove_super_volume("SV1")

    assert excinfo.value.serial == "SV1"


# ── 复活（REMOVED → UNKNOWN + 拓扑恢复） ──────────────────────────


def test_revive_super_volume_restores_unknown_and_topology(db, repo, volumes):
    """输入 已 REMOVED 的超级卷 → 期望输出 state 置回 UNKNOWN，释放的子卷重新挂回 USING。"""
    repo.reg_super_volume(
        H.make_super_volume("SV1", volumes=["V1", "V2"], name="S")
    )
    repo.remove_super_volume("SV1")

    repo.revive_super_volume("SV1")

    got = repo.get_super_volume("SV1")
    assert got is not None
    assert got.state is SuperVolumeState.UNKNOWN
    assert got.name == "S"
    assert got.volumes == ["V1", "V2"]


def test_revive_super_volume_missing_raises(repo):
    """输入 复活不存在的超级卷 → 期望输出 SuperVolumeNotFoundError。"""
    with pytest.raises(SuperVolumeNotFoundError):
        repo.revive_super_volume("GHOST")


def test_revive_super_volume_not_removed_raises(db, repo, volumes):
    """输入 复活未处于 REMOVED 的超级卷 → 期望输出 SuperVolumeNotRemovedError 且状态不变。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    with pytest.raises(SuperVolumeNotRemovedError) as excinfo:
        repo.revive_super_volume("SV1")

    assert excinfo.value.state is SuperVolumeState.HEALTHY
    assert repo.get_super_volume("SV1").state is SuperVolumeState.HEALTHY


def test_revive_super_volume_does_not_restore_replaced_member(db, repo, volumes):
    """输入 先用 replace 换下一个成员、再软删并复活 → 期望输出 被换下的旧卷保持 REPLACED（不随复活恢复）。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1", "V2"]))
    repo.replace_volume("SV1", "V1", "V3", datetime.now())
    repo.remove_super_volume("SV1")

    repo.revive_super_volume("SV1")

    assert repo.get_super_volume("SV1").volumes == ["V2", "V3"]
    row = next(r for r in _structure_rows(db) if r.volume_id == "V1")
    assert row.state is SuperVolumeRelationState.REPLACED


def test_revive_super_volume_rejects_removed_child(db, repo, volumes):
    """输入 软删后子卷也被移除 → 期望输出 SubVolumeUnavailableError 且整体回滚。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1", "V2"]))
    repo.remove_super_volume("SV1")
    db.repos["volume"].remove_volume("V1")  # 已非 USING，可移除

    with pytest.raises(SubVolumeUnavailableError):
        repo.revive_super_volume("SV1")

    # 回滚：超级卷仍 REMOVED，两条关联仍是 SUPER_VOLUME_REMOVED
    assert (
        repo.get_super_volume("SV1", exclude_removed=False).state
        is SuperVolumeState.REMOVED
    )
    assert {r.state for r in _structure_rows(db)} == {
        SuperVolumeRelationState.SUPER_VOLUME_REMOVED
    }


# ── 主键迁移 ──────────────────────────────────────────────────────


def test_update_serial_cascades_to_structures(db, repo, volumes):
    """输入 超级卷改名 → 期望输出 新 serial 存在、旧 serial 消失、关联随之迁移且 name 保留。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1", "V2"]))

    repo.update_super_volume_serial("SV1", "SV1-NEW")

    assert repo.is_exist("SV1-NEW") is True
    assert repo.is_exist("SV1") is False
    migrated = repo.get_super_volume("SV1-NEW")
    assert migrated.name == "SV1"
    assert migrated.volumes == ["V1", "V2"]
    assert H.count(db, SuperVolumeStructureModel) == 2


def test_update_serial_same_serial_is_noop(db, repo, volumes):
    """输入 新旧 serial 相同 → 期望输出 提前返回，记录与 name 均不变。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    repo.update_super_volume_serial("SV1", "SV1")

    assert repo.is_exist("SV1") is True
    assert repo.get_super_volume("SV1").name == "SV1"
    assert repo.get_super_volume("SV1").volumes == ["V1"]


def test_update_serial_missing_raises_value_error(repo):
    """输入 迁移不存在的超级卷 → 期望输出 ValueError。"""
    with pytest.raises(SuperVolumeNotFoundError):
        repo.update_super_volume_serial("GHOST", "NEW")


def test_update_serial_to_existing_serial_raises_and_rolls_back(db, repo, volumes):
    """输入 把 SV1 改名为已存在的 SV2 → 期望输出 SuperVolumeAlreadyRegisteredError 且两条记录都还在。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.reg_super_volume(H.make_super_volume("SV2", volumes=["V2"]))

    with pytest.raises(SuperVolumeAlreadyRegisteredError):
        repo.update_super_volume_serial("SV1", "SV2")

    assert repo.is_exist("SV1") is True
    assert repo.is_exist("SV2") is True


def test_update_serial_to_removed_serial_raises(db, repo, volumes):
    """输入 把 SV1 改名为一条 REMOVED 墓碑占用的 serial → 期望输出 SuperVolumeAlreadyRemovedError。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.reg_super_volume(H.make_super_volume("SV2", volumes=["V2"]))
    repo.remove_super_volume("SV2")

    with pytest.raises(SuperVolumeAlreadyRemovedError):
        repo.update_super_volume_serial("SV1", "SV2")

    assert repo.is_exist("SV1") is True
    assert repo.is_exist("SV2") is True
    assert repo.get_super_volume("SV2") is None


# ── 静态方法 ──────────────────────────────────────────────────────


def test_model_to_dict_is_static_and_complete():
    """输入 内存构造的模型行 + 子卷列表 → 期望输出 字段齐全且 volumes 原样透传。"""
    model = SuperVolumeModel(
        serial="SV1",
        name="n",
        svtype="copy",
        method="copy",
        state=SuperVolumeState.HEALTHY,
        info="i",
    )

    assert SuperVolumeRepository._model_to_dict(model, ["V1", "V2"]) == {
        "serial": "SV1",
        "name": "n",
        "svtype": "copy",
        "method": "copy",
        "add_time": None,
        "last_check_time": None,
        "state": SuperVolumeState.HEALTHY,
        "info": "i",
        "volumes": ["V1", "V2"],
    }
