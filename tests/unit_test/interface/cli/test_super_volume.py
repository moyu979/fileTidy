# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：interface/cli/super_volume —— SuperVolumeCLI 超级卷子命令。

目的：验证超级卷子命令的交互流程（`do_reg` 的名称/类型/info/子卷采集、
`do_add_volume`/`do_replace_volume` 的参数采集）、查询、字段更新、info 操作与移除，
确认对 `super_volume_service` 的调用契约与输出文本。
``do_remove_volumes`` 随「摘子卷」功能暂缓（TODO P1）一并停用。

输入：`builtins.input` 应答序列、命令行参数字符串、仅含 `super_volume_service`
的 app 替身。
期望输出：打印文本、传给 `super_volume_service` 的位置/关键字参数。
"""

from __future__ import annotations

import types

import pytest

from domain.storage.super_volume.enum import SuperVolumeState
from interface.cli.super_volume import SuperVolumeCLI


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


def _cli(service=None) -> SuperVolumeCLI:
    """构造持有假（或缺失）超级卷服务的 SuperVolumeCLI。"""
    return SuperVolumeCLI(app=types.SimpleNamespace(super_volume_service=service))


def _patch_input(monkeypatch, answers) -> None:
    """把 `builtins.input` 替换为依次吐出 answers 的队列（耗尽后返回空串）。"""
    queue = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(queue, ""))


# ── KV / info 辅助 ─────────────────────────────────────────────


def test_parse_kv_pairs():
    """输入 'a:1' 与 'b: two' → 输出 {'a':'1','b':'two'}。"""
    assert SuperVolumeCLI._parse_kv_pairs("a:1", "b: two") == {"a": "1", "b": "two"}


def test_parse_kv_pairs_invalid_raises():
    """输入不含冒号的 'no-colon' → 期望抛 ValueError。"""
    with pytest.raises(ValueError):
        SuperVolumeCLI._parse_kv_pairs("no-colon")


def test_interactive_kv(monkeypatch):
    """输入多行 'key:value' 后接空行 → 输出对应字典。"""
    _patch_input(monkeypatch, ["a:1", "b: two words", ""])

    assert _cli()._interactive_kv() == {"a": "1", "b": "two words"}


def test_print_info_diff(capsys):
    """输入新旧 info 且存在差异 → 输出表头 'key' 与全部键行。"""
    SuperVolumeCLI._print_info_diff({"a": "1"}, {"a": "2", "b": "3"})

    out = capsys.readouterr().out
    assert "key" in out
    assert "a" in out and "b" in out


def test_print_info_diff_empty_prints_no_change(capsys):
    """输入两个空 info → 输出 'info 无变化。'。"""
    SuperVolumeCLI._print_info_diff({}, {})

    assert "info 无变化。" in capsys.readouterr().out


# ── 服务可用性 ─────────────────────────────────────────────────


def test_missing_service_message(capsys):
    """输入 app=None → 输出 True 并打印“应用未初始化，无法执行超级卷操作”。"""
    cli = SuperVolumeCLI(app=None)

    assert cli._missing_service() is True
    assert "应用未初始化" in capsys.readouterr().out


def test_missing_service_when_service_absent(capsys):
    """输入 app 存在但 super_volume_service=None → 输出 True 并打印“超级卷服务不可用”。"""
    assert _cli()._missing_service() is True
    assert "超级卷服务不可用" in capsys.readouterr().out


# ── do_reg ─────────────────────────────────────────────────────


def test_do_reg_registers_super_volume(monkeypatch, capsys):
    """输入名称/类型 copy/info/两个子卷 → 关键字参数完整传给 reg_super_volume。"""
    service = _FakeService(reg_super_volume="SV1")
    _patch_input(monkeypatch, ["sv-name", "1", "info-x", "V1", "V2", ""])

    _cli(service).do_reg("")

    assert "成功登记超级卷: SV1" in capsys.readouterr().out
    assert service.calls == [
        (
            "reg_super_volume",
            (),
            {
                "name": "sv-name",
                "svtype": "copy",
                "info": "info-x",
                "volumes": ["V1", "V2"],
            },
        )
    ]


def test_do_reg_empty_optionals(monkeypatch):
    """名称与 info 留空、类型 2 → name/info 为 None，svtype 为 snapraid_raid5。"""
    service = _FakeService(reg_super_volume="SV1")
    _patch_input(monkeypatch, ["", "2", "", "V1", ""])

    _cli(service).do_reg("")

    kwargs = service.calls[0][2]
    assert kwargs["name"] is None
    assert kwargs["info"] is None
    assert kwargs["svtype"] == "snapraid_raid5"
    assert kwargs["volumes"] == ["V1"]


def test_do_reg_requires_at_least_one_volume(monkeypatch, capsys):
    """子卷列表为空 → 输出“至少需要提供一个子卷 ID”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, ["", "1", "", ""])

    _cli(service).do_reg("")

    assert "错误: 至少需要提供一个子卷 ID。" in capsys.readouterr().out
    assert service.calls == []


def test_do_reg_retries_invalid_type(monkeypatch, capsys):
    """类型先给非法编号再给合法编号 → 输出重试提示并最终登记。"""
    service = _FakeService(reg_super_volume="SV1")
    _patch_input(monkeypatch, ["", "9", "1", "", "V1", ""])

    _cli(service).do_reg("")

    assert "无效输入，请重新选择。" in capsys.readouterr().out
    assert service.calls[0][2]["svtype"] == "copy"


def test_do_reg_prints_error_on_service_exception(monkeypatch, capsys):
    """登记时服务抛异常 → 输出 '错误: ...' 而非崩溃。"""
    service = _FakeService(reg_super_volume=RuntimeError("子卷不存在"))
    _patch_input(monkeypatch, ["", "1", "", "V1", ""])

    _cli(service).do_reg("")

    assert "错误: 子卷不存在" in capsys.readouterr().out


def test_do_reg_accepts_q_terminator(monkeypatch):
    """子卷输入以 'q' 结束 → q 不被计入 volumes。"""
    service = _FakeService(reg_super_volume="SV1")
    _patch_input(monkeypatch, ["", "1", "", "V1", "q"])

    _cli(service).do_reg("")

    assert service.calls[0][2]["volumes"] == ["V1"]


# ── 子卷管理 ───────────────────────────────────────────────────


def test_do_add_volume_calls_service(monkeypatch, capsys):
    """输入目标序列号与一个子卷 → add_volume 收到序列号与子卷 ID。"""
    service = _FakeService(add_volume="SV1")
    _patch_input(monkeypatch, ["SV1", "V9"])

    _cli(service).do_add_volume("")

    assert "添加成功: SV1" in capsys.readouterr().out
    assert service.calls == [("add_volume", ("SV1", "V9"), {})]


def test_do_add_volume_uses_positional_args(capsys):
    """位置参数齐全 → 直接用参，不再交互采集。"""
    service = _FakeService(add_volume="SV1")

    _cli(service).do_add_volume("SV1 V9")

    assert service.calls == [("add_volume", ("SV1", "V9"), {})]


def test_do_add_volume_requires_serial(monkeypatch, capsys):
    """目标超级卷序列号留空 → 输出错误，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, [""])

    _cli(service).do_add_volume("")

    assert "序列号不能为空。" in capsys.readouterr().out
    assert service.calls == []


def test_do_add_volume_prints_error_on_exception(monkeypatch, capsys):
    """添加时服务抛异常 → 输出 '错误: ...'。"""
    service = _FakeService(add_volume=RuntimeError("卷已占用"))
    _patch_input(monkeypatch, ["SV1", "V9"])

    _cli(service).do_add_volume("")

    assert "错误: 卷已占用" in capsys.readouterr().out


def test_do_replace_volume_calls_service(capsys):
    """输入超级卷/旧卷/新卷 → replace_volume 收到三者。"""
    service = _FakeService(replace_volume="SV1")

    _cli(service).do_replace_volume("SV1 V1 V2")

    assert "替换成功: SV1" in capsys.readouterr().out
    assert service.calls == [
        (
            "replace_volume",
            (),
            {"super_volume_serial": "SV1", "old_volume_id": "V1", "new_volume_id": "V2"},
        )
    ]


def test_do_replace_volume_prompts_when_args_missing(monkeypatch, capsys):
    """无位置参数 → 走交互采集三个序列号。"""
    service = _FakeService(replace_volume="SV1")
    _patch_input(monkeypatch, ["SV1", "V1", "V2"])

    _cli(service).do_replace_volume("")

    assert service.calls == [
        (
            "replace_volume",
            (),
            {"super_volume_serial": "SV1", "old_volume_id": "V1", "new_volume_id": "V2"},
        )
    ]


@pytest.mark.skip(reason="摘子卷功能暂缓（TODO P1：do_remove_volumes 已随仓储/ABC/service 停用）")
def test_do_remove_volumes_calls_service(monkeypatch, capsys):
    """输入目标序列号与一个子卷 → remove_volumes 收到序列号与子卷列表。"""
    service = _FakeService(remove_volumes="SV1")
    _patch_input(monkeypatch, ["SV1", "V1", ""])

    _cli(service).do_remove_volumes("")

    assert "移除成功: SV1" in capsys.readouterr().out
    assert service.calls == [
        (
            "remove_volumes",
            (),
            {"super_volume_serial": "SV1", "volume_ids": ["V1"]},
        )
    ]


@pytest.mark.skip(reason="摘子卷功能暂缓（TODO P1：do_remove_volumes 已随仓储/ABC/service 停用）")
def test_do_remove_volumes_requires_volume_ids(monkeypatch, capsys):
    """子卷列表为空 → 输出错误，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, ["SV1", ""])

    _cli(service).do_remove_volumes("")

    assert "错误: 至少需要提供一个子卷 ID。" in capsys.readouterr().out
    assert service.calls == []


# ── 查询 ───────────────────────────────────────────────────────


def test_do_list_empty_prints_placeholder(capsys):
    """输入 list 且服务返回空列表 → 输出 '（无超级卷）'。"""
    _cli(_FakeService(list_super_volumes=[])).do_list("")

    assert "（无超级卷）" in capsys.readouterr().out


def test_do_list_prints_each_super_volume(capsys):
    """输入 list 且服务返回 2 个超级卷 → 两个字符串都被打印。"""
    _cli(_FakeService(list_super_volumes=["SV1", "SV2"])).do_list("")

    out = capsys.readouterr().out
    assert "SV1" in out and "SV2" in out


def test_do_get_empty_target_falls_back_to_list(monkeypatch):
    """输入目标留空 → 期望退回 do_list（调用 list_super_volumes）。"""
    service = _FakeService(list_super_volumes=[])
    _patch_input(monkeypatch, [""])

    _cli(service).do_get("")

    assert [call[0] for call in service.calls] == ["list_super_volumes"]


def test_do_get_found_prints_super_volume(monkeypatch, capsys):
    """输入已知序列号 → 输出该超级卷内容，不输出“未找到”。"""
    service = _FakeService(get_super_volume="SV-OBJ")
    _patch_input(monkeypatch, ["SV1"])

    _cli(service).do_get("")

    out = capsys.readouterr().out
    assert "SV-OBJ" in out and "未找到该超级卷" not in out
    assert service.calls == [("get_super_volume", ("SV1",), {})]


def test_do_get_not_found_prints_message(monkeypatch, capsys):
    """加载返回 None → 输出 '未找到该超级卷。'。"""
    service = _FakeService(get_super_volume=None)
    _patch_input(monkeypatch, ["GHOST"])

    _cli(service).do_get("")

    assert "未找到该超级卷。" in capsys.readouterr().out


# ── 字段更新 ───────────────────────────────────────────────────


def test_do_set_name_prints_transition(capsys):
    """输入 'SV1 new' → 服务收到 ('SV1','new') 并输出 '名称: a → b'。"""
    service = _FakeService(set_name=("a", "b"))

    _cli(service).do_set_name("SV1 new")

    assert service.calls == [("set_name", ("SV1", "new"), {})]
    assert "名称: a → b" in capsys.readouterr().out


def test_do_set_svtype_prints_transition(monkeypatch, capsys):
    """输入 set_svtype SV1 + 菜单编号 2 → 服务收到 'snapraid_raid5'。"""
    service = _FakeService(set_svtype=("copy", "snapraid_raid5"))
    _patch_input(monkeypatch, ["2"])

    _cli(service).do_set_svtype("SV1")

    assert service.calls == [("set_svtype", ("SV1", "snapraid_raid5"), {})]
    assert "类型: copy → snapraid_raid5" in capsys.readouterr().out


def test_do_set_state_prints_enum_values(monkeypatch, capsys):
    """输入 set_state SV1 + 菜单编号 2 → 输出 '状态: unknown → healthy'。"""
    service = _FakeService(
        set_state=(SuperVolumeState.UNKNOWN, SuperVolumeState.HEALTHY)
    )
    _patch_input(monkeypatch, ["2"])

    _cli(service).do_set_state("SV1")

    assert "状态: unknown → healthy" in capsys.readouterr().out
    assert service.calls == [("set_state", ("SV1", SuperVolumeState.HEALTHY), {})]


def test_do_set_serial_prints_transition(capsys):
    """输入 'old new' → 输出 '序列号: old → new'。"""
    service = _FakeService(set_serial=("old", "new"))

    _cli(service).do_set_serial("old new")

    assert "序列号: old → new" in capsys.readouterr().out


# ── info 操作 ──────────────────────────────────────────────────


def test_do_set_info_with_kv_args_calls_service(capsys):
    """输入 'SV1 a:1 b:2' → 服务收到 {'a':'1','b':'2'} 并打印 info 对比表。"""
    service = _FakeService(set_info=({}, {"a": "1", "b": "2"}))

    _cli(service).do_set_info("SV1 a:1 b:2")

    assert service.calls == [("set_info", ("SV1", {"a": "1", "b": "2"}), {})]
    assert "key" in capsys.readouterr().out


def test_do_set_info_invalid_kv_prints_error(capsys):
    """输入 'SV1 a:1 bad' → 输出解析错误原文，不调用服务。"""
    service = _FakeService()

    _cli(service).do_set_info("SV1 a:1 bad")

    assert "无法解析「bad」" in capsys.readouterr().out
    assert service.calls == []


def test_do_append_info_with_kv_args_calls_service(capsys):
    """输入 'SV1 n:1 x:2' → 服务收到 ('SV1', {'n':'1','x':'2'})。"""
    service = _FakeService(append_info=({}, {"n": "1", "x": "2"}))

    _cli(service).do_append_info("SV1 n:1 x:2")

    assert service.calls == [("append_info", ("SV1", {"n": "1", "x": "2"}), {})]


def test_do_append_info_interactive_when_args_short(monkeypatch):
    """输入 'SV1' 后交互补全序列号与键值 → 服务收到交互解析出的字典。"""
    service = _FakeService(append_info=({}, {"n": "1"}))
    _patch_input(monkeypatch, ["SV1", "n:1", ""])

    _cli(service).do_append_info("SV1")

    assert service.calls == [("append_info", ("SV1", {"n": "1"}), {})]


def test_do_delete_info_with_key(capsys):
    """输入 'SV1 note' → 服务收到 ('SV1','note') 并打印 info 对比。"""
    service = _FakeService(delete_info=({"note": "x"}, {}))

    _cli(service).do_delete_info("SV1 note")

    assert service.calls == [("delete_info", ("SV1", "note"), {})]
    assert "key" in capsys.readouterr().out


def test_do_delete_info_requires_key(monkeypatch, capsys):
    """输入 'SV1' 后交互键名留空 → 输出“键名不能为空”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, [""])

    _cli(service).do_delete_info("SV1")

    assert "键名不能为空。" in capsys.readouterr().out
    assert service.calls == []


# ── 移除与返回 ─────────────────────────────────────────────────


def test_do_remove_prints_confirmation(capsys):
    """输入 'SV1' → 输出 '已移除超级卷: SV1'。"""
    service = _FakeService()

    _cli(service).do_remove("SV1")

    assert service.calls == [("remove_super_volume", ("SV1",), {})]
    assert "已移除超级卷: SV1" in capsys.readouterr().out


def test_do_remove_prints_error_on_exception(capsys):
    """移除时服务抛异常 → 输出 '错误: ...' 而非“已移除”。"""
    service = _FakeService(remove_super_volume=RuntimeError("被占用"))

    _cli(service).do_remove("SV1")

    out = capsys.readouterr().out
    assert "错误: 被占用" in out
    assert "已移除超级卷" not in out


def test_do_back_and_eof_return_true(capsys):
    """输入 back / EOF → 均返回 True（结束子命令循环），EOF 额外换行。"""
    cli = _cli()

    assert cli.do_back("") is True
    assert cli.do_EOF("") is True
    assert capsys.readouterr().out == "\n"
