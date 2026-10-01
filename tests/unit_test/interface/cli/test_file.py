# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：interface/cli/file —— FileCLI 文件操作子命令（move / copy）。

目的：验证 `--key value` 风格参数解析（`_parse_args`）、服务可用性检查，
以及 `do_move` / `do_copy` 的参数校验、CSV 校验、时间解析与对 `file_service`
的调用契约和错误输出；全部在假服务与临时 CSV 下进行。

输入：命令行参数字符串、临时 CSV 文件、仅含 `file_service` 的 app 替身。
期望输出：打印文本与传给 `file_service` 的关键字参数（含 DataFrame 与 add_time）。
"""

from __future__ import annotations

import types
from datetime import datetime
from pathlib import Path

from interface.cli.file import FileCLI


class _FakeService:
    """记录调用并按需返回预置结果的假服务（预置值为异常实例时抛出）。"""

    def __init__(self, **returns):
        self.calls: list[tuple[str, tuple, dict]] = []
        self._returns = returns

    def __getattr__(self, name):
        def _call(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            outcome = self._returns.get(name)
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome

        return _call


def _cli(service=None) -> FileCLI:
    """构造持有假（或缺失）文件服务的 FileCLI。"""
    return FileCLI(app=types.SimpleNamespace(file_service=service))


def _write_csv(path: Path, header: str, rows: list[str] | None = None) -> Path:
    """写出 CSV 文件并返回路径（默认写一行数据）。"""
    body = rows if rows is not None else ["h1,h2,1,file.bin"]
    path.write_text(header + "\n" + "\n".join(body) + "\n", encoding="utf-8")
    return path


_FULL_HEADER = "sha256,hash,size,path"


def _move_args(csv_path: Path, extra: str = "") -> str:
    """拼出包含全部必需参数的 move/copy 参数串。"""
    return (
        f"--src-vol V1 --src-root /s --src-dir a "
        f"--dst-vol V2 --dst-root /d --dst-dir b --csv {csv_path} {extra}"
    ).strip()


# ── 参数解析 ───────────────────────────────────────────────────


def test_parse_args():
    """输入 '--src a --dst b --force' → 输出含无值 flag（值为空串）的字典。"""
    cli = FileCLI(app=None)

    assert cli._parse_args("--src a --dst b --force") == {
        "src": "a",
        "dst": "b",
        "force": "",
    }


def test_parse_args_ignores_bare_tokens():
    """输入裸露 token 'junk' → 被忽略，仅解析 --key（有/无值两种情况）。"""
    cli = FileCLI(app=None)

    assert cli._parse_args("junk --a --b c") == {"a": "", "b": "c"}


def test_parse_args_empty_string():
    """输入空字符串 → 输出空字典。"""
    assert FileCLI(app=None)._parse_args("") == {}


# ── 服务可用性 ─────────────────────────────────────────────────


def test_missing_service_message(capsys):
    """输入 app=None → 输出 True 并打印“应用未初始化”。"""
    assert FileCLI(app=None)._missing_service() is True
    assert "应用未初始化" in capsys.readouterr().out


def test_missing_service_when_service_absent(capsys):
    """输入 app 存在但 file_service=None → 输出 True 并打印“文件服务不可用”。"""
    assert _cli()._missing_service() is True
    assert "文件服务不可用" in capsys.readouterr().out


def test_do_move_short_circuits_without_service(capsys):
    """输入 app=None 后执行 move → 输出错误提示，不解析参数。"""
    FileCLI(app=None).do_move("--src-vol V1")

    assert "应用未初始化" in capsys.readouterr().out


# ── do_move ────────────────────────────────────────────────────


def test_do_move_missing_args(capsys):
    """输入空参数 → 输出全部缺失参数名与 help 提示，不调用服务。"""
    service = _FakeService()

    _cli(service).do_move("")

    out = capsys.readouterr().out
    assert "缺少必要参数: src-vol" in out
    assert "使用 help move 查看用法" in out
    assert service.calls == []


def test_do_move_missing_csv_file(capsys, tmp_path):
    """输入不存在的 CSV 路径 → 输出“CSV 文件不存在”，不调用服务。"""
    service = _FakeService()

    _cli(service).do_move(_move_args(tmp_path / "nope.csv"))

    assert "错误: CSV 文件不存在" in capsys.readouterr().out
    assert service.calls == []


def test_do_move_missing_column(capsys, tmp_path):
    """输入缺 path 列的 CSV → 输出“CSV 缺少列「path」”，不调用服务。"""
    csv_path = _write_csv(tmp_path / "bad.csv", "sha256,hash,size")
    service = _FakeService()

    _cli(service).do_move(_move_args(csv_path))

    assert "错误: CSV 缺少列「path」" in capsys.readouterr().out
    assert service.calls == []


def test_do_move_invalid_time(capsys, tmp_path):
    """输入非法 --time → 输出时间格式错误，不调用服务。"""
    csv_path = _write_csv(tmp_path / "ok.csv", _FULL_HEADER)
    service = _FakeService()

    _cli(service).do_move(_move_args(csv_path, '--time not-a-date'))

    assert "错误: 时间格式无效「not-a-date」" in capsys.readouterr().out
    assert service.calls == []


def test_do_move_calls_service_with_dataframe(capsys, tmp_path):
    """输入合法参数与两行 CSV → move_file 收到全部路径参数、DataFrame 与 add_time=None。"""
    csv_path = _write_csv(
        tmp_path / "ok.csv", _FULL_HEADER, ["a,b,1,f1", "c,d,2,f2"]
    )
    service = _FakeService()

    _cli(service).do_move(_move_args(csv_path))

    assert "移动完成，共处理 2 个文件。" in capsys.readouterr().out
    name, args, kwargs = service.calls[0]
    assert name == "move_file" and args == ()
    assert kwargs["src_volume"] == "V1"
    assert kwargs["src_root"] == "/s"
    assert kwargs["src_dir"] == "a"
    assert kwargs["dst_volume"] == "V2"
    assert kwargs["dst_root"] == "/d"
    assert kwargs["dst_dir"] == "b"
    assert kwargs["add_time"] is None
    assert list(kwargs["df"].columns) == ["sha256", "hash", "size", "path"]
    assert len(kwargs["df"]) == 2


def test_do_move_parses_iso_time(capsys, tmp_path):
    """输入 ISO 格式 --time → move_file 收到等值的 datetime 对象。"""
    csv_path = _write_csv(tmp_path / "ok.csv", _FULL_HEADER)
    service = _FakeService()

    _cli(service).do_move(_move_args(csv_path, '--time 2026-06-23T12:00:00'))

    assert service.calls[0][2]["add_time"] == datetime(2026, 6, 23, 12, 0, 0)


def test_do_move_prints_error_on_service_exception(capsys, tmp_path):
    """移动时服务抛异常 → 输出 '错误: 移动失败: ...'。"""
    csv_path = _write_csv(tmp_path / "ok.csv", _FULL_HEADER)
    service = _FakeService(move_file=RuntimeError("目标已存在"))

    _cli(service).do_move(_move_args(csv_path))

    assert "错误: 移动失败: 目标已存在" in capsys.readouterr().out


# ── do_copy ────────────────────────────────────────────────────


def test_do_copy_missing_args(capsys):
    """输入空参数 → 输出全部缺失参数名与 copy 的 help 提示，不调用服务。"""
    service = _FakeService()

    _cli(service).do_copy("")

    out = capsys.readouterr().out
    assert "缺少必要参数: src-vol" in out
    assert "使用 help copy 查看用法" in out
    assert service.calls == []


def test_do_copy_calls_service_with_dataframe(capsys, tmp_path):
    """输入合法参数 → copy_file 收到全部路径参数与 DataFrame，并输出处理条数。"""
    csv_path = _write_csv(tmp_path / "ok.csv", _FULL_HEADER)
    service = _FakeService()

    _cli(service).do_copy(_move_args(csv_path))

    assert "复制完成，共处理 1 个文件。" in capsys.readouterr().out
    name, args, kwargs = service.calls[0]
    assert name == "copy_file" and args == ()
    assert kwargs["src_volume"] == "V1" and kwargs["dst_dir"] == "b"
    assert len(kwargs["df"]) == 1


def test_do_copy_prints_error_on_service_exception(capsys, tmp_path):
    """复制时服务抛异常 → 输出 '错误: 复制失败: ...'。"""
    csv_path = _write_csv(tmp_path / "ok.csv", _FULL_HEADER)
    service = _FakeService(copy_file=RuntimeError("磁盘已满"))

    _cli(service).do_copy(_move_args(csv_path))

    assert "错误: 复制失败: 磁盘已满" in capsys.readouterr().out


# ── 返回 ───────────────────────────────────────────────────────


def test_do_back_and_eof_return_true(capsys):
    """输入 back / EOF → 均返回 True（结束子命令循环），EOF 额外换行。"""
    cli = _cli()

    assert cli.do_back("") is True
    assert cli.do_EOF("") is True
    assert capsys.readouterr().out == "\n"
