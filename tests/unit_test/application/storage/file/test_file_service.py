# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：application/storage/file/file_service —— 文件服务用例。

目的：验证文件夹扫描登记、CSV 登记、按清单移动/复制的数据校验与
持久化调用。仓储为内存替身，哈希器打桩。

输入：临时文件 / DataFrame。
期望输出：NewFile 列表、相对路径计算与 move/copy 后的行状态。
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import pytest

import application.storage.file.file_service as service_mod
from application.storage.file.file_service import FileService
from domain.storage.file.new_file import NewFile


@pytest.fixture
def events(monkeypatch):
    box = []
    monkeypatch.setattr(service_mod, "log_event", box.append)
    return box


@pytest.fixture
def svc(fake_file_repo, fake_hasher, events):
    return FileService(file_repo=fake_file_repo, hasher=fake_hasher)


def test_register_folder_recurses_and_relativizes(tmp_path, svc, fake_file_repo):
    """嵌套文件 → 每个文件一行，now_path 相对 datas 根。"""
    (tmp_path / "datas" / "sub").mkdir(parents=True)
    (tmp_path / "datas" / "root.txt").write_text("r", encoding="utf-8")
    (tmp_path / "datas" / "sub" / "inner.txt").write_text("i", encoding="utf-8")

    result = svc.register_folder(
        folder_path=str(tmp_path / "datas"),
        volume_serial="V1",
        volume_path=str(tmp_path / "datas"),
    )

    assert len(result) == 2
    paths = sorted(fake_file_repo.rows.keys())
    assert paths == [("V1", "root.txt"), ("V1", "sub/inner.txt")]
    row = fake_file_repo.rows[("V1", "root.txt")]
    assert row["sha512"] == "sha512:" + str((tmp_path / "datas" / "root.txt"))
    assert row["size"] == 1


def test_register_by_csv(tmp_path, svc, fake_file_repo):
    """CSV 行 → 登记；卷根内路径取相对、根外路径回退文件名。"""
    root = tmp_path / "v"
    (root / "datas").mkdir(parents=True)
    inside = str(root / "datas" / "a.txt")
    outside = str(tmp_path / "outside.txt")
    df = pd.DataFrame([
        {"sha512": "s1", "hash": "m1", "size": 3, "path": inside},
        {"sha512": "s2", "hash": "m2", "size": 4, "path": outside},
    ])
    result = svc.register_by_csv(df=df, volume_serial="V1", volume_path=str(root / "datas"))
    assert len(result) == 2
    assert ("V1", "a.txt") in fake_file_repo.rows
    assert ("V1", "outside.txt") in fake_file_repo.rows
    assert fake_file_repo.rows[("V1", "a.txt")]["state"].value == "unknown"


def _prime_db(fake_file_repo, sha512="sha", md5="md", path="dir/a.txt"):
    nf = NewFile(
        sha512=sha512, md5=md5, size=1,
        add_time=datetime(2026, 1, 1),
        path=path, now_path=path, now_volume="V1",
    )
    fake_file_repo.reg_file(nf)


def test_move_file_by_csv(svc, fake_file_repo, tmp_path):
    """清单一致 → move_file 更新位置并触发 FileMoved。"""
    _prime_db(fake_file_repo)
    dst_root = tmp_path / "dst"
    (dst_root / "dir").mkdir(parents=True)
    df = pd.DataFrame([{
        "sha512": "sha", "hash": "md", "size": 1,
        "path": str(dst_root / "dir" / "a.txt"),
    }])

    svc.move_file(
        src_volume="V1", src_root="", src_dir="dir",
        dst_volume="V2", dst_root=str(dst_root), dst_dir="dir",
        df=df,
    )
    assert ("V2", "dir/a.txt") in fake_file_repo.rows
    assert ("V1", "dir/a.txt") not in fake_file_repo.rows


def test_move_file_mismatch_raises(svc, fake_file_repo, tmp_path):
    """DB 与 CSV 键不一致 → ValueError。"""
    _prime_db(fake_file_repo)
    df = pd.DataFrame([{
        "sha512": "sha", "hash": "md", "size": 1,
        "path": str(tmp_path / "dir" / "other.txt"),
    }])
    with pytest.raises(ValueError, match="清单不一致"):
        svc.move_file("V1", "", "dir", "V2", str(tmp_path), "dir", df)


def test_copy_file_by_csv(svc, fake_file_repo, tmp_path):
    """清单一致 → copy_file 新增目标行，源行保留。"""
    _prime_db(fake_file_repo)
    dst_root = tmp_path / "dst"
    (dst_root / "dir").mkdir(parents=True)
    df = pd.DataFrame([{
        "sha512": "sha", "hash": "md", "size": 1,
        "path": str(dst_root / "dir" / "a.txt"),
    }])
    svc.copy_file("V1", "", "dir", "V2", str(dst_root), "dir", df)
    assert ("V1", "dir/a.txt") in fake_file_repo.rows
    assert ("V2", "dir/a.txt") in fake_file_repo.rows
