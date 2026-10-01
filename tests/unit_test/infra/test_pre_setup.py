# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/pre_setup.py —— 启动前准备阶段（目录结构 / 外部工具 / 运行环境 / 阶段编排）。

目的（测什么）：
- `setup_file_structure`：data_dir 回退到 `./datas`、递归建目录、data_dir 是文件时报错、
  assets 缺失/是文件时报错、`merge_dir` 的调用参数与 OSError 透传、合并「补缺不覆盖」；
- `check_external_tools` / `prepare_environment`：占位实现返回 None 且只写日志；
- `pre_setup`：三步严格按 目录 → 工具 → 环境 顺序执行、data_dir 透传、任一步失败即中断；
- `main`：`--data-dir` 解析为 Path（缺省 `./datas`）后交给 `pre_setup`。

输入：`tmp_path` 临时目录、monkeypatch 替换的 `merge_dir` / 模块 `__file__` / 三个步骤函数、caplog。

期望输出：目录被创建并补入 assets 内容，异常类型为 `NotADirectoryError` / `FileNotFoundError`，
       日志含中文步骤标记，`pre_setup` 的各步返回 None 且顺序固定。
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pytest

import infra.pre_setup as pre_setup_mod


# ── setup_file_structure ──────────────────────────────────────────


def test_setup_creates_data_dir_and_merges_assets(tmp_path):
    """输入 tmp_path 下不存在的 data_dir → 期望输出 目录被创建且 assets/settings 被补齐。"""
    data_dir = tmp_path / "data"

    assert pre_setup_mod.setup_file_structure(data_dir) is None

    assert data_dir.is_dir()
    assert (data_dir / "settings" / "database.yaml").is_file()
    assert (data_dir / "settings" / "log.yaml").is_file()


def test_setup_keeps_existing_files(tmp_path):
    """输入 data_dir 内已有同名设置文件 → 期望输出 合并时保留原内容（补缺不覆盖）。"""
    data_dir = tmp_path / "data"
    (data_dir / "settings").mkdir(parents=True)
    (data_dir / "settings" / "database.yaml").write_text("# custom\n", encoding="utf-8")

    pre_setup_mod.setup_file_structure(data_dir)

    assert (data_dir / "settings" / "database.yaml").read_text(encoding="utf-8") == "# custom\n"


def test_setup_creates_nested_data_dir(tmp_path):
    """输入 多级均不存在的 data_dir → 期望输出 递归创建成功。"""
    data_dir = tmp_path / "a" / "b" / "c"

    pre_setup_mod.setup_file_structure(data_dir)

    assert data_dir.is_dir()


def test_setup_none_falls_back_to_dot_datas(tmp_path, monkeypatch, caplog):
    """输入 data_dir=None 且 cwd 指向 tmp_path → 期望输出 使用 ./datas 并记录日志。"""
    monkeypatch.chdir(tmp_path)

    with caplog.at_level(logging.INFO, logger="infra.pre_setup"):
        pre_setup_mod.setup_file_structure(None)

    assert (tmp_path / "datas").is_dir()
    assert (tmp_path / "datas" / "settings").is_dir()
    assert "data_dir 未指定" in caplog.text


def test_setup_data_dir_is_file_raises(tmp_path):
    """输入 data_dir 指向已存在的文件 → 期望输出 NotADirectoryError 且文件内容不被改动。"""
    target = tmp_path / "afile"
    target.write_text("keep-me", encoding="utf-8")

    with pytest.raises(NotADirectoryError, match="指向一个已存在的文件"):
        pre_setup_mod.setup_file_structure(target)

    assert target.read_text(encoding="utf-8") == "keep-me"


def test_setup_missing_assets_raises_file_not_found(tmp_path, monkeypatch):
    """输入 模块 __file__ 指向不含 assets 的临时目录 → 期望输出 FileNotFoundError。"""
    monkeypatch.setattr(pre_setup_mod, "__file__", str(tmp_path / "pkg" / "pre_setup.py"))

    with pytest.raises(FileNotFoundError, match="assets 目录不存在"):
        pre_setup_mod.setup_file_structure(tmp_path / "data")


def test_setup_assets_is_file_raises(tmp_path, monkeypatch):
    """输入 assets 路径是一个文件 → 期望输出 NotADirectoryError。"""
    (tmp_path / "assets").write_text("not-a-dir", encoding="utf-8")
    monkeypatch.setattr(pre_setup_mod, "__file__", str(tmp_path / "pkg" / "pre_setup.py"))

    with pytest.raises(NotADirectoryError, match="assets 路径是一个文件"):
        pre_setup_mod.setup_file_structure(tmp_path / "data")


def test_setup_calls_merge_dir_with_assets_and_data_dir(tmp_path, monkeypatch):
    """输入 打桩 merge_dir → 期望输出 恰好收到 (仓库 assets 目录, data_dir) 一次。"""
    calls: list[tuple[Path, Path]] = []
    monkeypatch.setattr(
        pre_setup_mod,
        "merge_dir",
        lambda src, dst: calls.append((Path(src), Path(dst))),
    )
    data_dir = tmp_path / "data"

    pre_setup_mod.setup_file_structure(data_dir)

    assert calls == [
        (Path(pre_setup_mod.__file__).resolve().parent.parent / "assets", data_dir)
    ]


def test_setup_propagates_oserror_from_merge(tmp_path, monkeypatch):
    """输入 merge_dir 抛 OSError → 期望输出 原样透传（不被吞掉）。"""

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(pre_setup_mod, "merge_dir", boom)

    with pytest.raises(OSError, match="disk full"):
        pre_setup_mod.setup_file_structure(tmp_path / "data")


# ── check_external_tools / prepare_environment ────────────────────


def test_check_external_tools_is_noop_with_log(caplog):
    """输入 无（占位实现）→ 期望输出 返回 None 且日志含「检查外部工具」。"""
    with caplog.at_level(logging.INFO, logger="infra.pre_setup"):
        assert pre_setup_mod.check_external_tools() is None

    assert "检查外部工具" in caplog.text


def test_prepare_environment_is_noop_with_log(caplog):
    """输入 无（占位实现）→ 期望输出 返回 None 且日志含「准备运行时环境」。"""
    with caplog.at_level(logging.INFO, logger="infra.pre_setup"):
        assert pre_setup_mod.prepare_environment() is None

    assert "准备运行时环境" in caplog.text


# ── pre_setup ─────────────────────────────────────────────────────


def test_pre_setup_runs_three_steps_in_order(tmp_path, monkeypatch):
    """输入 打桩三个步骤函数 → 期望输出 按 目录 → 工具 → 环境 顺序执行并透传 data_dir。"""
    order: list[tuple[str, object]] = []
    monkeypatch.setattr(
        pre_setup_mod, "setup_file_structure", lambda d: order.append(("setup", d))
    )
    monkeypatch.setattr(
        pre_setup_mod, "check_external_tools", lambda: order.append(("tools", None))
    )
    monkeypatch.setattr(
        pre_setup_mod, "prepare_environment", lambda: order.append(("env", None))
    )
    data_dir = tmp_path / "data"

    assert pre_setup_mod.pre_setup(argparse.Namespace(data_dir=data_dir)) is None

    assert [name for name, _ in order] == ["setup", "tools", "env"]
    assert order[0][1] == data_dir


def test_pre_setup_logs_start_and_done(tmp_path, monkeypatch, caplog):
    """输入 打桩步骤 + 真实日志 → 期望输出 日志含阶段开始与完成标记。"""
    monkeypatch.setattr(pre_setup_mod, "setup_file_structure", lambda d: None)
    monkeypatch.setattr(pre_setup_mod, "check_external_tools", lambda: None)
    monkeypatch.setattr(pre_setup_mod, "prepare_environment", lambda: None)

    with caplog.at_level(logging.INFO, logger="infra.pre_setup"):
        pre_setup_mod.pre_setup(argparse.Namespace(data_dir=tmp_path))

    assert "pre_setup 阶段开始" in caplog.text
    assert "pre_setup 阶段完成" in caplog.text


def test_pre_setup_end_to_end_creates_data_dir(tmp_path):
    """输入 真实三步 + tmp_path/data → 期望输出 数据目录与默认设置文件就位。"""
    data_dir = tmp_path / "data"

    pre_setup_mod.pre_setup(argparse.Namespace(data_dir=data_dir))

    assert data_dir.is_dir()
    assert (data_dir / "settings" / "hash.yaml").is_file()


def test_pre_setup_propagates_step_error_and_skips_rest(tmp_path, monkeypatch):
    """输入 setup_file_structure 抛异常 → 期望输出 异常透传且后续两步不执行。"""
    order: list[str] = []

    def boom(data_dir):
        raise NotADirectoryError("bad data dir")

    monkeypatch.setattr(pre_setup_mod, "setup_file_structure", boom)
    monkeypatch.setattr(
        pre_setup_mod, "check_external_tools", lambda: order.append("tools")
    )
    monkeypatch.setattr(
        pre_setup_mod, "prepare_environment", lambda: order.append("env")
    )

    with pytest.raises(NotADirectoryError, match="bad data dir"):
        pre_setup_mod.pre_setup(argparse.Namespace(data_dir=tmp_path))

    assert order == []


# ── main ──────────────────────────────────────────────────────────


def test_main_passes_cli_data_dir(tmp_path, monkeypatch):
    """输入 sys.argv 带 --data-dir → 期望输出 pre_setup 收到该 Path。"""
    captured: dict = {}
    monkeypatch.setattr(
        pre_setup_mod,
        "pre_setup",
        lambda args: captured.setdefault("data_dir", args.data_dir),
    )
    monkeypatch.setattr("sys.argv", ["pre_setup", "--data-dir", str(tmp_path / "d")])

    pre_setup_mod.main()

    assert captured["data_dir"] == tmp_path / "d"


def test_main_defaults_to_dot_datas(monkeypatch):
    """输入 sys.argv 无 --data-dir → 期望输出 pre_setup 收到默认 Path('./datas')。"""
    captured: dict = {}
    monkeypatch.setattr(
        pre_setup_mod,
        "pre_setup",
        lambda args: captured.setdefault("data_dir", args.data_dir),
    )
    monkeypatch.setattr("sys.argv", ["pre_setup"])

    pre_setup_mod.main()

    assert captured["data_dir"] == Path("./datas")
