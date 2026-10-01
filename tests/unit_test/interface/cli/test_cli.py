# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：interface/cli/cli —— FileTidyCLI 主调度器。

目的：验证主 CLI 的职责仅限于「装配子 CLI + 按命令名分发路由」：
`do_device/do_volume/do_super_device/do_super_volume/do_file` 及其简写各自
把控制权交给对应子 CLI 的 `cmdloop()`；退出命令 `quit/exit/EOF` 返回真值
以结束 cmdloop；未知命令走 `default` 打印提示；`main()` 负责异常兜底。

输入：App 替身（None 或哨兵对象）、命令方法名、KeyboardInterrupt。
期望输出：被路由到的子 CLI 名序列、打印文本、返回值与 SystemExit 退出码。
"""

from __future__ import annotations

import pytest

import interface.cli.cli as cli_mod
from interface.cli.cli import FileTidyCLI

_SUB_CLI_ATTRS = (
    "_device_cli",
    "_file_cli",
    "_volume_cli",
    "_super_device_cli",
    "_super_volume_cli",
)


class _LoopRecorder:
    """替身子 CLI：只记录自己的 cmdloop 被调用。"""

    def __init__(self, name: str, sink: list) -> None:
        self.name = name
        self._sink = sink

    def cmdloop(self, *args, **kwargs):
        """记录一次调用并返回 None。"""
        self._sink.append(self.name)


def _cli_with_recorders(app=None):
    """构造主 CLI 并把 5 个子 CLI 全部换成替身。"""
    cli = FileTidyCLI(app=app)
    calls: list[str] = []
    for attr in _SUB_CLI_ATTRS:
        setattr(cli, attr, _LoopRecorder(attr, calls))
    return cli, calls


def test_init_creates_all_sub_clis_with_same_app():
    """传入 app 哨兵 → 5 个子 CLI 都被实例化且持有同一个 app。"""
    app = object()

    cli = FileTidyCLI(app=app)

    assert cli._device_cli.app is app
    assert cli._file_cli.app is app
    assert cli._volume_cli.app is app
    assert cli._super_device_cli.app is app
    assert cli._super_volume_cli.app is app


def test_init_accepts_none_app():
    """不传 app → 各子 CLI 的 app 为 None，构造不报错。"""
    cli = FileTidyCLI()

    assert cli._device_cli.app is None
    assert cli._volume_cli.app is None


def test_prompt_and_intro_are_set():
    """类属性 → prompt 为 "filetidy> "，intro 含 "FileTidy" 提示。"""
    assert FileTidyCLI.prompt == "filetidy> "
    assert "FileTidy" in FileTidyCLI.intro
    assert "quit" in FileTidyCLI.intro


@pytest.mark.parametrize(
    ("method", "expected_sub_cli"),
    [
        ("do_device", "_device_cli"),
        ("do_dev", "_device_cli"),
        ("do_file", "_file_cli"),
        ("do_f", "_file_cli"),
        ("do_volume", "_volume_cli"),
        ("do_vol", "_volume_cli"),
        ("do_super_device", "_super_device_cli"),
        ("do_sdev", "_super_device_cli"),
        ("do_super_volume", "_super_volume_cli"),
        ("do_svol", "_super_volume_cli"),
    ],
)
def test_group_command_enters_matching_sub_cli(method, expected_sub_cli):
    """调用分组命令（含简写）→ 只有对应子 CLI 的 cmdloop 被调用一次，返回 None。"""
    cli, calls = _cli_with_recorders(app=None)

    result = getattr(cli, method)("")

    assert result is None
    assert calls == [expected_sub_cli]


def test_do_quit_returns_true_and_prints_farewell(capsys):
    """执行 quit → 返回 True（结束 cmdloop）并打印 "再见！"。"""
    cli = FileTidyCLI(app=None)

    assert cli.do_quit("") is True
    assert "再见！" in capsys.readouterr().out


def test_do_exit_delegates_to_quit(capsys):
    """执行 exit → 与 quit 等价（返回 True，打印同一句告别）。"""
    cli = FileTidyCLI(app=None)

    assert cli.do_exit("") is True
    assert "再见！" in capsys.readouterr().out


def test_do_eof_returns_true(capsys):
    """执行 EOF（Ctrl+D）→ 返回 True 并打印告别。"""
    cli = FileTidyCLI(app=None)

    assert cli.do_EOF("") is True
    assert "再见！" in capsys.readouterr().out


def test_default_prints_unknown_command_hint(capsys):
    """输入未定义命令 → 打印未知命令原文与 help 提示，不抛异常。"""
    cli = FileTidyCLI(app=None)

    cli.default("frobnicate 1 2")

    out = capsys.readouterr().out
    assert "未知命令: frobnicate 1 2" in out
    assert "输入 'help' 查看可用命令" in out


def test_main_runs_cmdloop_with_given_app(monkeypatch):
    """调用 main(app) → 用同一个 app 构造 FileTidyCLI 并执行 cmdloop。"""
    seen: list = []

    class _FakeCLI:
        def __init__(self, app=None):
            self.app = app

        def cmdloop(self):
            seen.append(self.app)

    monkeypatch.setattr(cli_mod, "FileTidyCLI", _FakeCLI)

    cli_mod.main(app="APP")

    assert seen == ["APP"]


def test_main_swallows_keyboard_interrupt(monkeypatch, capsys):
    """cmdloop 抛 KeyboardInterrupt → 打印中断提示并以 SystemExit(0) 退出。"""
    class _InterruptingCLI:
        def __init__(self, app=None):
            self.app = app

        def cmdloop(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(cli_mod, "FileTidyCLI", _InterruptingCLI)

    with pytest.raises(SystemExit) as excinfo:
        cli_mod.main()

    assert excinfo.value.code == 0
    assert "程序被中断，再见！" in capsys.readouterr().out
