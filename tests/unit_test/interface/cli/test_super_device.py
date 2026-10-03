# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：interface/cli/super_device —— SuperDeviceCLI 超级设备子命令。

目的：验证超级设备子命令的交互流程（`do_reg` 的序列号/类型/上线策略/子设备
采集）、`do_get` 的「序列号 vs 路径」分派、字段更新、info 操作与子设备增删改，
确认对 `super_device_service` 的调用契约与输出文本。

输入：`builtins.input` 应答序列、命令行参数字符串、仅含 `super_device_service`
的 app 替身（`is_path` 被替换为桩）。
期望输出：打印文本、传给 `super_device_service` 的位置/关键字参数。
"""

from __future__ import annotations

import types

import pytest

import interface.cli.super_device as sd_mod
from domain.storage.super_device.enum import SuperDeviceState
from interface.cli.super_device import SuperDeviceCLI


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


def _cli(service=None) -> SuperDeviceCLI:
    """构造持有假（或缺失）超级设备服务的 SuperDeviceCLI。"""
    return SuperDeviceCLI(app=types.SimpleNamespace(super_device_service=service))


def _patch_input(monkeypatch, answers) -> None:
    """把 `builtins.input` 替换为依次吐出 answers 的队列（耗尽后返回空串）。"""
    queue = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(queue, ""))


# ── KV / info 辅助 ─────────────────────────────────────────────


def test_parse_kv_pairs():
    """输入 'a:1' 与 'b: two' → 输出 {'a':'1','b':'two'}。"""
    assert SuperDeviceCLI._parse_kv_pairs("a:1", "b: two") == {"a": "1", "b": "two"}


def test_parse_kv_pairs_invalid_raises():
    """输入不含冒号的 'no-colon' → 期望抛 ValueError。"""
    with pytest.raises(ValueError):
        SuperDeviceCLI._parse_kv_pairs("no-colon")


def test_interactive_kv(monkeypatch):
    """输入多行 'key:value' 后接空行 → 输出对应字典。"""
    _patch_input(monkeypatch, ["a:1", "b: two words", ""])

    assert _cli()._interactive_kv() == {"a": "1", "b": "two words"}


def test_print_info_diff(capsys):
    """输入新旧 info 且存在差异 → 输出表头 'key' 与全部键行。"""
    SuperDeviceCLI._print_info_diff({"a": "1"}, {"a": "2", "b": "3"})

    out = capsys.readouterr().out
    assert "key" in out
    assert "a" in out and "b" in out


def test_print_info_diff_empty_prints_no_change(capsys):
    """输入两个空 info → 输出 'info 无变化。'。"""
    SuperDeviceCLI._print_info_diff({}, {})

    assert "info 无变化。" in capsys.readouterr().out


# ── 服务可用性 ─────────────────────────────────────────────────


def test_missing_service_message(capsys):
    """输入 app=None → 输出 True 并打印“应用未初始化，无法执行超级设备操作”。"""
    cli = SuperDeviceCLI(app=None)

    assert cli._missing_service() is True
    assert "应用未初始化" in capsys.readouterr().out


def test_missing_service_when_service_absent(capsys):
    """输入 app 存在但 super_device_service=None → 输出 True 并打印“超级设备服务不可用”。"""
    assert _cli()._missing_service() is True
    assert "超级设备服务不可用" in capsys.readouterr().out


# ── do_reg ─────────────────────────────────────────────────────


def test_do_reg_registers_super_device(monkeypatch, capsys):
    """输入序列号/名称/类型 single/上线策略 y/两个子设备 → data 完整传给服务。"""
    service = _FakeService(reg_super_device_manual="SD1")
    _patch_input(monkeypatch, ["SD1", "my-sd", "1", "note", "y", "D1", "D2", ""])

    _cli(service).do_reg("")

    assert "成功登记超级设备: SD1" in capsys.readouterr().out
    name, args, kwargs = service.calls[0]
    assert name == "reg_super_device_manual" and kwargs == {}
    assert args[0] == {
        "serial": "SD1",
        "name": "my-sd",
        "sdtype": "single",
        "need_all_devices_online": True,
        "devices": ["D1", "D2"],
        "info": "note",
    }


def test_do_reg_auto_serial_and_n_flag(monkeypatch):
    """序列号/名称/info 留空、上线策略 n → serial/name/info 为 None，need_all 为 False。"""
    service = _FakeService(reg_super_device_manual="SD1")
    _patch_input(monkeypatch, ["", "", "2", "", "n", "D1", ""])

    _cli(service).do_reg("")

    data = service.calls[0][1][0]
    assert data["serial"] is None
    assert data["name"] is None
    assert data["info"] is None
    assert data["sdtype"] == "raidz"
    assert data["need_all_devices_online"] is False


def test_do_reg_requires_at_least_one_device(monkeypatch, capsys):
    """子设备列表为空 → 输出“至少需要一个设备”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, ["SD1", "", "1", "", "y", ""])

    _cli(service).do_reg("")

    assert "错误: 至少需要一个设备。" in capsys.readouterr().out
    assert service.calls == []


def test_do_reg_retries_invalid_type_and_yn(monkeypatch, capsys):
    """类型与 y/n 先给非法值再给合法值 → 输出重试提示并最终登记。"""
    service = _FakeService(reg_super_device_manual="SD1")
    _patch_input(monkeypatch, ["SD1", "", "9", "1", "", "maybe", "y", "D1", ""])

    _cli(service).do_reg("")

    out = capsys.readouterr().out
    assert "无效输入，请重新选择。" in out
    assert "无效输入，请输入 y 或 n。" in out
    assert service.calls[0][1][0]["devices"] == ["D1"]


def test_do_reg_prints_error_on_service_exception(monkeypatch, capsys):
    """登记时服务抛异常 → 输出 '错误: ...' 而非崩溃。"""
    service = _FakeService(reg_super_device_manual=RuntimeError("序列号重复"))
    _patch_input(monkeypatch, ["SD1", "", "1", "", "y", "D1", ""])

    _cli(service).do_reg("")

    assert "错误: 序列号重复" in capsys.readouterr().out


# ── 查询 ───────────────────────────────────────────────────────


def test_do_list_empty_prints_placeholder(capsys):
    """输入 list 且服务返回空列表 → 输出 '（无超级设备）'。"""
    _cli(_FakeService(list_super_devices=[])).do_list("")

    assert "（无超级设备）" in capsys.readouterr().out


def test_do_get_empty_target_falls_back_to_list(monkeypatch):
    """输入目标留空 → 期望退回 do_list（调用 list_super_devices）。"""
    service = _FakeService(list_super_devices=[])
    _patch_input(monkeypatch, [""])

    _cli(service).do_get("")

    assert [call[0] for call in service.calls] == ["list_super_devices"]


def test_do_get_by_serial(monkeypatch, capsys):
    """目标不是路径 → 以 serial 关键字调用 load_super_device 并打印结果。"""
    service = _FakeService(load_super_device="SD-S1")
    monkeypatch.setattr(sd_mod, "is_path", lambda value: False)
    _patch_input(monkeypatch, ["SD1"])

    _cli(service).do_get("")

    assert "SD-S1" in capsys.readouterr().out
    assert service.calls == [("load_super_device", (), {"serial": "SD1"})]


def test_do_get_by_path(monkeypatch, capsys):
    """目标是路径 → 以 super_device_path 关键字调用 load_super_device。"""
    service = _FakeService(load_super_device="SD-S2")
    monkeypatch.setattr(sd_mod, "is_path", lambda value: True)
    _patch_input(monkeypatch, ["/mnt/sd2"])

    _cli(service).do_get("")

    assert service.calls == [
        ("load_super_device", (), {"super_device_path": "/mnt/sd2"})
    ]
    assert "SD-S2" in capsys.readouterr().out


def test_do_get_not_found_prints_message(monkeypatch, capsys):
    """加载返回 None → 输出 '未找到该超级设备。'。"""
    service = _FakeService(load_super_device=None)
    monkeypatch.setattr(sd_mod, "is_path", lambda value: False)
    _patch_input(monkeypatch, ["GHOST"])

    _cli(service).do_get("")

    assert "未找到该超级设备。" in capsys.readouterr().out


# ── 字段更新 ───────────────────────────────────────────────────


def test_do_set_name_prints_transition(capsys):
    """输入 'SD1 new' → 服务收到 ('SD1','new') 并输出 '名称: a → b'。"""
    service = _FakeService(set_name=("a", "b"))

    _cli(service).do_set_name("SD1 new")

    assert service.calls == [("set_name", ("SD1", "new"), {})]
    assert "名称: a → b" in capsys.readouterr().out


def test_do_set_sdtype_prints_transition(monkeypatch, capsys):
    """输入 set_sdtype SD1 + 菜单编号 2 → 服务收到 raidz 字符串。"""
    service = _FakeService(set_sdtype=("single", "raidz"))
    _patch_input(monkeypatch, ["2"])

    _cli(service).do_set_sdtype("SD1")

    assert service.calls == [("set_sdtype", ("SD1", "raidz"), {})]
    assert "类型: single → raidz" in capsys.readouterr().out


def test_do_set_state_prints_enum_values(monkeypatch, capsys):
    """输入 set_state SD1 + 菜单编号 2 → 输出 '状态: unknown → healthy'。"""
    service = _FakeService(
        set_state=(SuperDeviceState.UNKNOWN, SuperDeviceState.HEALTHY)
    )
    _patch_input(monkeypatch, ["2"])

    _cli(service).do_set_state("SD1")

    assert "状态: unknown → healthy" in capsys.readouterr().out
    assert service.calls == [("set_state", ("SD1", SuperDeviceState.HEALTHY), {})]


def test_do_set_capacity_rejects_non_integer(capsys):
    """输入 'SD1 abc' → 输出“容量必须为整数（字节）”，不调用服务。"""
    service = _FakeService()

    _cli(service).do_set_capacity("SD1 abc")

    assert "容量必须为整数（字节）。" in capsys.readouterr().out
    assert service.calls == []


def test_do_set_need_all_devices_online_accepts_y(monkeypatch, capsys):
    """输入 set_need_all_devices_online SD1 + 'y' → 服务收到布尔 True。"""
    service = _FakeService(set_need_all_devices_online=(False, True))
    _patch_input(monkeypatch, ["y"])

    _cli(service).do_set_need_all_devices_online("SD1")

    assert service.calls == [
        ("set_need_all_devices_online", ("SD1", True), {})
    ]
    assert "need_all_devices_online: False → True" in capsys.readouterr().out


def test_do_set_need_all_devices_online_retries(monkeypatch, capsys):
    """先给非法回答再给 'n' → 输出重试提示并最终传递 False。"""
    service = _FakeService(set_need_all_devices_online=(True, False))
    _patch_input(monkeypatch, ["maybe", "n"])

    _cli(service).do_set_need_all_devices_online("SD1")

    assert "无效输入，请输入 y 或 n。" in capsys.readouterr().out
    assert service.calls[0][1] == ("SD1", False)


def test_do_set_serial_prints_transition(capsys):
    """输入 'old new' → 输出 '序列号: old → new'。"""
    service = _FakeService(set_serial=("old", "new"))

    _cli(service).do_set_serial("old new")

    assert "序列号: old → new" in capsys.readouterr().out


# ── info 操作 ──────────────────────────────────────────────────


def test_do_set_info_with_kv_args_calls_service(capsys):
    """输入 'SD1 a:1 b:2' → 服务收到 {'a':'1','b':'2'} 并打印 info 对比表。"""
    service = _FakeService(set_info=({}, {"a": "1", "b": "2"}))

    _cli(service).do_set_info("SD1 a:1 b:2")

    assert service.calls == [("set_info", ("SD1", {"a": "1", "b": "2"}), {})]
    assert "key" in capsys.readouterr().out


def test_do_set_info_invalid_kv_prints_error(capsys):
    """输入 'SD1 a:1 bad' → 输出解析错误原文，不调用服务。"""
    service = _FakeService()

    _cli(service).do_set_info("SD1 a:1 bad")

    assert "无法解析「bad」" in capsys.readouterr().out
    assert service.calls == []


def test_do_append_info_with_kv_args_calls_service(capsys):
    """输入 'SD1 n:1 x:2' → 服务收到 ('SD1', {'n':'1','x':'2'}) 并打印 info 对比。"""
    service = _FakeService(append_info=({}, {"n": "1", "x": "2"}))

    _cli(service).do_append_info("SD1 n:1 x:2")

    assert service.calls == [("append_info", ("SD1", {"n": "1", "x": "2"}), {})]
    assert "key" in capsys.readouterr().out


def test_do_append_info_interactive_when_args_short(monkeypatch):
    """输入 'SD1' 后交互补全序列号与键值 → 服务收到交互解析出的字典。"""
    service = _FakeService(append_info=({}, {"n": "1"}))
    _patch_input(monkeypatch, ["SD1", "n:1", ""])

    _cli(service).do_append_info("SD1")

    assert service.calls == [("append_info", ("SD1", {"n": "1"}), {})]


def test_do_delete_info_with_key(capsys):
    """输入 'SD1 note' → 服务收到 ('SD1','note') 并打印 info 对比。"""
    service = _FakeService(delete_info=({"note": "x"}, {}))

    _cli(service).do_delete_info("SD1 note")

    assert service.calls == [("delete_info", ("SD1", "note"), {})]
    assert "key" in capsys.readouterr().out


def test_do_delete_info_prompts_when_args_incomplete(monkeypatch, capsys):
    """输入 'SD1' 后交互补全键名 → 服务收到 ('SD1','note')。"""
    service = _FakeService(delete_info=({"note": "x"}, {}))
    _patch_input(monkeypatch, ["SD1", "note"])

    _cli(service).do_delete_info("SD1")

    assert service.calls == [("delete_info", ("SD1", "note"), {})]


# ── 子设备管理 ─────────────────────────────────────────────────


def test_do_add_device(capsys):
    """输入 'SD1 D3' → 服务收到 ('SD1','D3') 并输出添加成功提示。"""
    service = _FakeService()

    _cli(service).do_add_device("SD1 D3")

    assert service.calls == [("add_device", ("SD1", "D3"), {})]
    assert "子设备 D3 已添加到超级设备 SD1" in capsys.readouterr().out


def test_do_add_device_prints_error_on_exception(capsys):
    """添加时服务抛异常 → 输出 '错误: ...'。"""
    service = _FakeService(add_device=RuntimeError("设备不存在"))

    _cli(service).do_add_device("SD1 GHOST")

    assert "错误: 设备不存在" in capsys.readouterr().out


def test_do_add_device_requires_serials(monkeypatch, capsys):
    """参数不足且交互留空 → 输出“序列号不能为空”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, ["", ""])

    _cli(service).do_add_device("")

    assert "序列号不能为空。" in capsys.readouterr().out
    assert service.calls == []


def test_do_replace_device(capsys):
    """输入 'SD1 D1 D2' → 服务收到三个序列号并输出替换提示。"""
    service = _FakeService()

    _cli(service).do_replace_device("SD1 D1 D2")

    assert service.calls == [("replace_device", ("SD1", "D1", "D2"), {})]
    assert "子设备 D1 已替换为 D2" in capsys.readouterr().out


def test_do_replace_device_requires_serials(monkeypatch, capsys):
    """参数不足且交互留空 → 输出“所有序列号不能为空”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, ["", "", ""])

    _cli(service).do_replace_device("")

    assert "所有序列号不能为空。" in capsys.readouterr().out
    assert service.calls == []


@pytest.mark.skip(reason="摘子项功能暂缓（TODO P1：single 变体不变量待重新设计）")
def test_do_remove_device(capsys):
    """输入 'SD1 D1' → 服务收到两个序列号并输出移除提示。"""
    service = _FakeService()

    _cli(service).do_remove_device("SD1 D1")

    assert service.calls == [("remove_device", ("SD1", "D1"), {})]
    assert "子设备 D1 已从超级设备 SD1 移除" in capsys.readouterr().out


@pytest.mark.skip(reason="摘子项功能暂缓（TODO P1：single 变体不变量待重新设计）")
def test_do_remove_device_prints_error_on_exception(capsys):
    """移除子设备时服务抛异常 → 输出 '错误: ...'。"""
    service = _FakeService(remove_device=RuntimeError("结构占用"))

    _cli(service).do_remove_device("SD1 D1")

    assert "错误: 结构占用" in capsys.readouterr().out


# ── 移除与返回 ─────────────────────────────────────────────────


def test_do_remove_prints_confirmation(capsys):
    """输入 'SD1' → 输出 '已移除超级设备: SD1'。"""
    service = _FakeService()

    _cli(service).do_remove("SD1")

    assert service.calls == [("remove_super_device", ("SD1",), {})]
    assert "已移除超级设备: SD1" in capsys.readouterr().out


def test_do_remove_prints_error_on_exception(capsys):
    """移除时服务抛异常 → 输出 '错误: ...' 而非“已移除”。"""
    service = _FakeService(remove_super_device=RuntimeError("被占用"))

    _cli(service).do_remove("SD1")

    out = capsys.readouterr().out
    assert "错误: 被占用" in out
    assert "已移除超级设备" not in out


def test_do_back_and_eof_return_true(capsys):
    """输入 back / EOF → 均返回 True（结束子命令循环），EOF 额外换行。"""
    cli = _cli()

    assert cli.do_back("") is True
    assert cli.do_EOF("") is True
    assert capsys.readouterr().out == "\n"
