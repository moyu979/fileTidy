# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/storage/file_repository.py —— FileRepository 隔离单测。

目的（测什么）：
- 模块私有工具 `_path_as_text`（None / str / Path 归一）与实例工具 `_make_location_row` 的默认值；
- `reg_source` / `reg_location`：分别写 file_sources、file_locations，Path 转 POSIX、
  state 为空时落 ONLINE；重复登记时来源表跳过相同 (from_path, sha512, md5)、位置表静默覆盖；
- `transaction`：把两侧写入组合成同一事务，任一失败整体回滚；
- `list_by_volume_dir` 的前缀语义（同一目录、兄弟目录、空前缀、以文件路径当目录）；
- `move_file` / `copy_file` 的行迁移、源缺失 LookupError、目标非法时的 FK/唯一约束 IntegrityError；
- `is_exist()`：位置表中同时命中 sha512 与 md5 才判为存在。

输入：`tmp_path` 下每个用例独占的临时 SQLite 库 + `_helpers` 构造的领域对象。

期望输出：行数、字段值与异常类型符合仓储 docstring 与源码注释中的临时约定。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from domain.storage.file.enum import FileState
from domain.storage.file.repo import FileRepositoryABC
from infra.persistence.models import FileLocationsModel, FileSourcesModel
from infra.persistence.storage import file_repository as file_repository_mod
from tests.unit_test.infra.persistence import _helpers as H


@pytest.fixture
def db(tmp_path):
    """每个用例独占的临时 SQLite 库（仅建表）。"""
    handle = H.new_db(tmp_path / "file.db")
    yield handle
    handle.dispose()


@pytest.fixture
def repo(db):
    """绑定该库的 FileRepository。"""
    return db.repos["file"]


@pytest.fixture
def volumes(db):
    """两个已登记的卷 V1 / V2（文件位置的外键约束需要卷真实存在）。"""
    H.seed_volumes(db, ("V1", "V2"))
    return ("V1", "V2")


# ── 构造与私有工具 ────────────────────────────────────────────────


def test_repository_is_abc_implementation(db, repo):
    """输入 新建仓储 → 期望输出 是 FileRepositoryABC 实例且复用同一会话工厂。"""
    assert isinstance(repo, FileRepositoryABC)
    assert repo.session_factory is db.factory


def test_is_exist_returns_false_when_no_location_matches(repo, volumes):
    """输入 位置表为空 → 期望输出 False。"""
    assert repo.is_exist("s1", "m1") is False


def test_is_exist_returns_true_when_both_hashes_match(db, repo, volumes):
    """输入 已登记文件的 sha512 + md5 → 期望输出 True。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1"))

    assert repo.is_exist("s1", "m1") is True


def test_is_exist_requires_both_hashes_to_match(db, repo, volumes):
    """输入 仅 sha512 或仅 md5 命中 → 期望输出 False（须同时命中）。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1"))

    assert repo.is_exist("s1", "m-other") is False
    assert repo.is_exist("s-other", "m1") is False


def test_path_as_text_normalizes_none_str_and_path():
    """输入 None / 字符串 / Path → 期望输出 None / 原字符串 / POSIX 字符串。"""
    assert file_repository_mod._path_as_text(None) is None
    assert file_repository_mod._path_as_text("a/b.txt") == "a/b.txt"
    assert file_repository_mod._path_as_text(Path("a") / "b.txt") == "a/b.txt"


def test_make_location_row_fills_defaults(repo):
    """输入 _make_location_row 只给必需字段 → 期望输出 state=ONLINE、info=''、add_time 为当前时间。"""
    before = datetime.now()

    row = repo._make_location_row("s1", "m1", 3, "V1", "dir/a.txt")

    assert isinstance(row, FileLocationsModel)
    assert (row.sha512, row.md5, row.size) == ("s1", "m1", 3)
    assert (row.now_volume, row.now_path) == ("V1", "dir/a.txt")
    assert row.state is FileState.ONLINE
    assert row.info == ""
    assert row.add_time >= before


# ── reg_source / reg_location ─────────────────────────────────────


def test_reg_source_writes_source_row_only(db, repo, volumes):
    """输入 一个 NewFile → 期望输出 file_sources 1 行且字段一致，位置表不写。"""
    repo.reg_source(H.make_new_file(now_path="dir/a.txt", now_volume="V1"))

    with db.factory() as session:
        source = session.query(FileSourcesModel).one()
        assert session.query(FileLocationsModel).count() == 0

    assert source.from_path == "/outside/a.txt"
    assert (source.sha512, source.md5, source.size) == ("s1", "m1", 10)
    assert source.state is FileState.ONLINE


def test_reg_location_writes_location_row_only(db, repo, volumes):
    """输入 一个 NewFile → 期望输出 file_locations 1 行且字段一致，来源表不写。"""
    repo.reg_location(H.make_new_file(now_path="dir/a.txt", now_volume="V1"))

    with db.factory() as session:
        location = session.query(FileLocationsModel).one()
        assert session.query(FileSourcesModel).count() == 0

    assert location.now_volume == "V1"
    assert location.now_path == "dir/a.txt"
    assert location.state is FileState.ONLINE


def test_transaction_shares_session_between_both_writes(db, repo, volumes):
    """输入 在一个 transaction 内先写来源再写位置 → 期望输出 两表各 1 行。"""
    new_file = H.make_new_file(now_path="dir/a.txt", now_volume="V1")

    with repo.transaction() as session:
        repo.reg_source(new_file, session)
        repo.reg_location(new_file, session)

    assert H.count(db, FileSourcesModel) == 1
    assert H.count(db, FileLocationsModel) == 1


def test_transaction_rolls_back_source_when_location_fails(db, repo, volumes):
    """输入 同一事务内位置写入失败（卷不存在）→ 期望输出 来源写入一并回滚、两表无残留。"""
    with pytest.raises(IntegrityError):
        with repo.transaction() as session:
            repo.reg_source(H.make_new_file(now_path="dir/a.txt", now_volume="V1"), session)
            repo.reg_location(H.make_new_file(now_path="dir/a.txt", now_volume="GHOST"), session)

    assert H.count(db, FileSourcesModel) == 0
    assert H.count(db, FileLocationsModel) == 0


def test_registration_converts_path_objects_to_posix(db, repo, volumes):
    """输入 from_path / now_path 传 Path 对象 → 期望输出 落库为正斜杠相对/绝对路径字符串。"""
    H.register_file(
        repo,
        H.make_new_file(
            path=Path("/outside/deep/a.txt"),
            now_path=Path("dir") / "sub" / "a.txt",
            now_volume="V1",
        ),
    )

    with db.factory() as session:
        source = session.query(FileSourcesModel).one()
        location = session.query(FileLocationsModel).one()

    assert source.from_path == "/outside/deep/a.txt"
    assert location.now_path == "dir/sub/a.txt"


def test_registration_defaults_state_to_online_when_none(db, repo, volumes):
    """输入 NewFile.state=None → 期望输出 两张表都落 ONLINE（source 靠列默认、location 靠内联兜底）。"""
    H.register_file(repo, H.make_new_file(state=None, now_volume="V1"))

    with db.factory() as session:
        assert session.query(FileSourcesModel).one().state is FileState.ONLINE
        assert session.query(FileLocationsModel).one().state is FileState.ONLINE


def test_duplicate_registration_skips_source_and_overwrites_location(db, repo, volumes):
    """输入 同一来源（from_path + 哈希）登记两次 → 期望输出 file_sources 仍 1 行、file_locations 覆盖为 1 行。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1", info="first"))
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1", info="second"))

    with db.factory() as session:
        assert session.query(FileSourcesModel).count() == 1
        assert session.query(FileLocationsModel).count() == 1
        assert session.query(FileLocationsModel).one().info == "second"


def test_source_dedup_requires_path_and_hash_to_match(db, repo, volumes):
    """输入 仅路径相同或仅哈希相同 → 期望输出 各自新增 file_sources 行（须三者全同才跳过）。"""
    H.register_file(repo, H.make_new_file(
        sha512="s1", md5="m1", path="/outside/a.txt",
        now_path="dir/a.txt", now_volume="V1",
    ))
    H.register_file(repo, H.make_new_file(
        sha512="s1", md5="m1", path="/outside/b.txt",
        now_path="dir/b.txt", now_volume="V1",
    ))
    H.register_file(repo, H.make_new_file(
        sha512="s2", md5="m2", path="/outside/a.txt",
        now_path="dir/c.txt", now_volume="V1",
    ))

    assert H.count(db, FileSourcesModel) == 3


def test_same_path_on_different_volumes_creates_two_locations(db, repo, volumes):
    """输入 相同相对路径分别登记到 V1 / V2 → 期望输出 两条位置记录并存（主键含卷）。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1"))
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V2"))

    assert H.count(db, FileLocationsModel) == 2


# ── list_by_volume_dir ────────────────────────────────────────────


def test_list_by_volume_dir_matches_prefix_only(db, repo, volumes):
    """输入 同一目录、兄弟目录、空前缀、以文件路径当目录 → 期望输出 仅同目录文件被列出。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1"))
    H.register_file(repo, H.make_new_file(now_path="dir/sub/b.txt", now_volume="V1"))
    H.register_file(repo, H.make_new_file(now_path="dir2/c.txt", now_volume="V1"))
    H.register_file(repo, H.make_new_file(now_path="dir/d.txt", now_volume="V2"))

    assert [r["now_path"] for r in repo.list_by_volume_dir("V1", "dir")] == [
        "dir/a.txt",
        "dir/sub/b.txt",
    ]
    assert [r["now_path"] for r in repo.list_by_volume_dir("V1", "dir/sub")] == [
        "dir/sub/b.txt"
    ]
    # 空前缀会拼成 "/"，而卷内路径不带前导斜杠 → 空结果
    assert repo.list_by_volume_dir("V1", "") == []
    # 以文件自身路径当目录 → 拼成 "dir/a.txt/" → 空结果
    assert repo.list_by_volume_dir("V1", "dir/a.txt") == []


def test_list_by_volume_dir_returns_full_row_fields(db, repo, volumes):
    """输入 一个已登记文件 → 期望输出 字典包含哈希/大小/位置/状态等字段。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1"))

    rows = repo.list_by_volume_dir("V1", "dir")

    assert len(rows) == 1
    assert rows[0] == {
        "sha512": "s1",
        "md5": "m1",
        "size": 10,
        "now_volume": "V1",
        "now_path": "dir/a.txt",
        "state": FileState.ONLINE,
        "info": "",
        "add_time": H.FIXED_TIME,
    }


def test_list_by_volume_dir_ignores_state(db, repo, volumes):
    """输入 位置记录被标为 REMOVED → 期望输出 仍被列出（查询不过滤状态）。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1"))
    with db.factory() as session:
        session.query(FileLocationsModel).update({"state": FileState.REMOVED})
        session.commit()

    assert [r["now_path"] for r in repo.list_by_volume_dir("V1", "dir")] == ["dir/a.txt"]


# ── move_file / copy_file ─────────────────────────────────────────


def test_move_file_relocates_existing_row(db, repo, volumes):
    """输入 移动已登记文件到 V2 → 期望输出 源位置消失、目标位置出现且保留哈希/大小。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1"))

    repo.move_file("s1", "m1", "V1", "dir/a.txt", "V2", "moved/a.txt")

    with db.factory() as session:
        assert session.query(FileLocationsModel).count() == 1
        row = session.query(FileLocationsModel).one()
    assert (row.now_volume, row.now_path) == ("V2", "moved/a.txt")
    assert (row.sha512, row.md5, row.size) == ("s1", "m1", 10)


def test_move_file_updates_add_time(db, repo, volumes):
    """输入 显式传入 add_time → 期望输出 位置记录的 add_time 被替换为该值。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1"))
    new_time = datetime(2027, 5, 5, 1, 2, 3)

    repo.move_file("s1", "m1", "V1", "dir/a.txt", "V2", "moved/a.txt", add_time=new_time)

    with db.factory() as session:
        assert session.query(FileLocationsModel).one().add_time == new_time


def test_move_file_missing_source_raises_lookup_error(repo, volumes):
    """输入 源位置不存在 → 期望输出 LookupError 且提示含卷与路径。"""
    with pytest.raises(LookupError, match="源位置不存在"):
        repo.move_file("s1", "m1", "V1", "dir/none.txt", "V2", "x.txt")


def test_move_file_to_unknown_volume_raises_integrity_error(db, repo, volumes):
    """输入 移动到不存在的卷 → 期望输出 IntegrityError（外键）且原位置不变。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1"))

    with pytest.raises(IntegrityError):
        repo.move_file("s1", "m1", "V1", "dir/a.txt", "GHOST", "x.txt")

    with db.factory() as session:
        row = session.query(FileLocationsModel).one()
    assert (row.now_volume, row.now_path) == ("V1", "dir/a.txt")


def test_copy_file_creates_second_location(db, repo, volumes):
    """输入 复制到 V2 新路径 → 期望输出 两条位置记录，目标记录继承源的大小/状态/info。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1", info="tag"))

    repo.copy_file("s1", "m1", "V1", "dir/a.txt", "V2", "copy/a.txt")

    with db.factory() as session:
        rows = session.query(FileLocationsModel).all()
    assert len(rows) == 2
    target = next(r for r in rows if r.now_volume == "V2")
    assert target.now_path == "copy/a.txt"
    assert target.size == 10
    assert target.state is FileState.ONLINE
    assert target.info == "tag"


def test_copy_file_missing_source_raises_lookup_error(repo, volumes):
    """输入 复制不存在的源位置 → 期望输出 LookupError。"""
    with pytest.raises(LookupError, match="源位置不存在"):
        repo.copy_file("s1", "m1", "V1", "dir/none.txt", "V2", "x.txt")


def test_copy_file_onto_existing_location_raises_integrity_error(db, repo, volumes):
    """输入 复制到已存在的位置 → 期望输出 IntegrityError（主键冲突）且行数不变。"""
    H.register_file(repo, H.make_new_file(now_path="dir/a.txt", now_volume="V1"))

    with pytest.raises(IntegrityError):
        repo.copy_file("s1", "m1", "V1", "dir/a.txt", "V1", "dir/a.txt")

    assert H.count(db, FileLocationsModel) == 1
