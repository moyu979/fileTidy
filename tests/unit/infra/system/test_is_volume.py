# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/system/storage/volume/is_volume —— 卷目录结构判定。

目的：验证“仅含 datas/ 与 meta/ 两个子目录、meta/ 恰好一个文件”的判定规则。

输入：临时目录树。
期望输出：符合结构 True，否则 False。
"""

from __future__ import annotations

from infra.system.storage.volume.is_volume import is_volume


def _valid_volume(tmp_path):
    root = tmp_path / "vol"
    (root / "datas").mkdir(parents=True)
    (root / "meta").mkdir()
    (root / "meta" / "SERIAL-1").touch()
    return root


def test_valid_structure(tmp_path):
    """datas+meta+一个 meta 文件 → True。"""
    assert is_volume(str(_valid_volume(tmp_path))) is True


def test_missing_dirs(tmp_path):
    """缺少 datas 或 meta → False。"""
    root = tmp_path / "vol"
    root.mkdir()
    assert is_volume(str(root)) is False


def test_meta_missing_serial_file(tmp_path):
    """meta 为空 → False。"""
    root = tmp_path / "vol"
    (root / "datas").mkdir(parents=True)
    (root / "meta").mkdir()
    assert is_volume(str(root)) is False


def test_meta_multiple_files(tmp_path):
    """meta 有两个文件 → False。"""
    root = tmp_path / "vol"
    (root / "datas").mkdir(parents=True)
    (root / "meta").mkdir()
    (root / "meta" / "A").touch()
    (root / "meta" / "B").touch()
    assert is_volume(str(root)) is False


def test_extra_dir(tmp_path):
    """存在第三个目录 → False。"""
    root = tmp_path / "vol"
    (root / "datas").mkdir(parents=True)
    (root / "meta").mkdir()
    (root / "extra").mkdir()
    (root / "meta" / "S").touch()
    assert is_volume(str(root)) is False


def test_path_is_file(tmp_path):
    """路径本身是文件 → False。"""
    f = tmp_path / "a.txt"
    f.write_text("x", encoding="utf-8")
    assert is_volume(str(f)) is False
