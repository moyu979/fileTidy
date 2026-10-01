# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/storage/super_volume_repository.py —— SuperVolumeRepository 隔离单测。

目的（测什么）：
- 注册/查询/列表/`is_exist`，以及超级卷与子卷关联行（USING 过滤）的读写；
- `reg_super_volume` 的主行 + 关联行同事务写入，未知子卷触发外键 IntegrityError 并整体回滚；
- `add_volumes`：父不存在、子卷已属于其它超级卷（含 UNUSED 行，因唯一约束）→ ValueError；
  传入 UNUSED 结构的成员不会出现在 USING 视图里；
- `remove_volumes`：全部校验通过才更新（部分失败不产生半更新）；
- `remove_super_volume`：自身 REMOVED 且 USING 关联转 UNUSED；
- `update_super_volume` 的 svtype→type 映射与 state 归一化；`update_super_volume_serial` 的关联迁移与同值早退；
- 静态 `_model_to_dict`。

输入：`tmp_path` 下每个用例独占的临时 SQLite 库 + `_helpers` 构造的领域对象。

期望输出：查询结果、关联行状态与异常类型符合仓储 docstring。
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from domain.storage.super_device.enum import RelationState
from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.super_volume.repo import SuperVolumeRepositoryABC
from domain.storage.super_volume.structure import SuperVolumeStructure
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


def test_reg_super_volume_without_volumes(db, repo):
    """输入 空子卷列表 → 期望输出 主行落库且关联行数为 0。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=[]))

    assert repo.get_super_volume("SV1").volumes == []
    assert _structure_rows(db) == []


def test_reg_super_volume_unknown_volume_rolls_back(db, repo, volumes):
    """输入 子卷不存在 → 期望输出 IntegrityError（外键）且主行也回滚。"""
    with pytest.raises(IntegrityError):
        repo.reg_super_volume(H.make_super_volume("SV1", volumes=["GHOST"]))

    assert repo.is_exist("SV1") is False
    assert _structure_rows(db) == []


def test_reg_super_volume_duplicate_name_raises(db, repo, volumes):
    """输入 名称与已有超级卷重复 → 期望输出 IntegrityError（name 唯一约束）且未落库。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    with pytest.raises(IntegrityError):
        repo.reg_super_volume(
            H.make_super_volume("SV2", name="SV1", volumes=["V2"])
        )

    assert repo.is_exist("SV2") is False
    assert H.count(db, SuperVolumeModel) == 1


def test_get_super_volume_missing_returns_none(repo):
    """输入 不存在的 serial → 期望输出 None。"""
    assert repo.get_super_volume("GHOST") is None


def test_list_super_volume_returns_all(db, repo, volumes):
    """输入 空库/登记两个超级卷 → 期望输出 [] / 两个对象。"""
    assert repo.list_super_volume() == []

    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.reg_super_volume(H.make_super_volume("SV2", volumes=["V2"]))

    assert sorted(s.serial for s in repo.list_super_volume()) == ["SV1", "SV2"]


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
    with pytest.raises(ValueError, match="not found"):
        repo.update_super_volume("GHOST", name="x")


# ── add_volumes ───────────────────────────────────────────────────


def test_add_volumes_appends_members(db, repo, volumes):
    """输入 批量追加子卷 → 期望输出 volumes 增加且关联行 state=USING。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    repo.add_volumes(
        [
            SuperVolumeStructure("SV1", "V2", state=RelationState.USING, info="x"),
            SuperVolumeStructure("SV1", "V3", state=RelationState.USING, info="y"),
        ]
    )

    assert repo.get_super_volume("SV1").volumes == ["V1", "V2", "V3"]
    assert {r.state for r in _structure_rows(db)} == {RelationState.USING}


def test_add_volumes_missing_parent_raises(db, repo, volumes):
    """输入 父超级卷不存在 → 期望输出 ValueError 且无关联行写入。"""
    with pytest.raises(ValueError, match="不存在"):
        repo.add_volumes([SuperVolumeStructure("GHOST", "V1")])

    assert _structure_rows(db) == []


def test_add_volumes_rejects_volume_owned_by_another_super_volume(db, repo, volumes):
    """输入 子卷已属于其它超级卷 → 期望输出 ValueError 且不新增行。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.reg_super_volume(H.make_super_volume("SV2", volumes=["V2"]))

    with pytest.raises(ValueError, match="已属于"):
        repo.add_volumes([SuperVolumeStructure("SV1", "V2")])

    assert H.count(db, SuperVolumeStructureModel) == 2


def test_add_volumes_rejects_existing_unused_membership(db, repo, volumes):
    """输入 子卷在关联表中已有 UNUSED 行 → 期望输出 ValueError（唯一约束使重复插入不可行）。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.remove_volumes("SV1", ["V1"])

    with pytest.raises(ValueError, match="已属于"):
        repo.add_volumes([SuperVolumeStructure("SV1", "V1")])


def test_add_volumes_with_unused_state_is_not_visible_as_member(db, repo, volumes):
    """输入 以 UNUSED 状态追加子卷 → 期望输出 关联行落库但不计入 USING 成员视图。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))

    repo.add_volumes([SuperVolumeStructure("SV1", "V2", state=RelationState.UNUSED)])

    assert repo.get_super_volume("SV1").volumes == ["V1"]
    row = next(r for r in _structure_rows(db) if r.volume_id == "V2")
    assert row.state is RelationState.UNUSED


# ── remove_volumes ────────────────────────────────────────────────


def test_remove_volumes_releases_members(db, repo, volumes):
    """输入 移除 USING 成员 → 期望输出 关联行转 UNUSED 且不再计入成员视图。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1", "V2"]))

    repo.remove_volumes("SV1", ["V1"])

    assert repo.get_super_volume("SV1").volumes == ["V2"]
    row = next(r for r in _structure_rows(db) if r.volume_id == "V1")
    assert row.state is RelationState.UNUSED


def test_remove_volumes_partial_failure_does_not_update_anything(db, repo, volumes):
    """输入 待移除列表含非 USING 成员 → 期望输出 ValueError 且其余成员保持 USING（不半更新）。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1", "V2"]))

    with pytest.raises(ValueError, match="不是"):
        repo.remove_volumes("SV1", ["V1", "GHOST"])

    assert repo.get_super_volume("SV1").volumes == ["V1", "V2"]


def test_remove_volumes_missing_parent_raises(db, repo, volumes):
    """输入 父超级卷不存在 → 期望输出 ValueError。"""
    with pytest.raises(ValueError, match="不存在"):
        repo.remove_volumes("GHOST", ["V1"])


def test_remove_volumes_ignores_already_unused_member(db, repo, volumes):
    """输入 重复移除同一成员 → 期望输出 第二次 ValueError（已非 USING）。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1"]))
    repo.remove_volumes("SV1", ["V1"])

    with pytest.raises(ValueError, match="不是"):
        repo.remove_volumes("SV1", ["V1"])


# ── 软删除 ────────────────────────────────────────────────────────


def test_remove_super_volume_marks_removed_and_releases_members(db, repo, volumes):
    """输入 无外键冲突的超级卷 → 期望输出 自身 REMOVED、全部 USING 关联转 UNUSED。"""
    repo.reg_super_volume(H.make_super_volume("SV1", volumes=["V1", "V2"]))

    repo.remove_super_volume("SV1")

    assert repo.get_super_volume("SV1").state is SuperVolumeState.REMOVED
    rows = _structure_rows(db)
    assert len(rows) == 2
    assert {r.state for r in rows} == {RelationState.UNUSED}
    assert repo.get_super_volume("SV1").volumes == []


def test_remove_super_volume_missing_raises_value_error(repo):
    """输入 删除不存在的超级卷 → 期望输出 ValueError。"""
    with pytest.raises(ValueError, match="not found"):
        repo.remove_super_volume("GHOST")


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
    with pytest.raises(ValueError, match="not found"):
        repo.update_super_volume_serial("GHOST", "NEW")


# ── 静态方法 ──────────────────────────────────────────────────────


def test_model_to_dict_is_static_and_complete():
    """输入 内存构造的模型行 + 子卷列表 → 期望输出 字段齐全且 volumes 原样透传。"""
    model = SuperVolumeModel(
        serial="SV1",
        name="n",
        type="copy",
        method="copy",
        state=SuperVolumeState.HEALTHY,
        info="i",
    )

    assert SuperVolumeRepository._model_to_dict(model, ["V1", "V2"]) == {
        "serial": "SV1",
        "name": "n",
        "type": "copy",
        "method": "copy",
        "add_time": None,
        "last_check_time": None,
        "state": SuperVolumeState.HEALTHY,
        "info": "i",
        "volumes": ["V1", "V2"],
    }
