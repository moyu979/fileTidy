# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：interface/cli/device —— DeviceCLI 与设备规格辅助函数。

目的：验证设备子命令的交互/参数解析（`_collect_device_spec` 的菜单录入、
`_merge_spec_info` 的 info 合并、`_parse_kv_pairs`/`_interactive_kv`/
`_print_info_diff`）以及各 `do_*` 对 `device_service` 的调用契约与输出文本。

输入：`builtins.input` 应答序列、命令行参数字符串、仅含 `device_service` 的 app 替身。
期望输出：打印文本、传给 `device_service` 的位置/关键字参数，以及异常分支的提示语。
"""

from __future__ import annotations

import json
import types

import pytest

from domain.storage.device.enum import DeviceState
from interface.cli.device import DeviceCLI, _collect_device_spec, _merge_spec_info


class _FakeService:
    """记录调用并按需返回预置结果的假服务。

    预置值为异常实例时抛出该异常，用于覆盖 `except` 分支。
    """

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


def _app(service=None):
    """构造仅含 device_service 的 app 替身（service 为 None 表示服务不可用）。"""
    return types.SimpleNamespace(device_service=service)


def _cli(service=None) -> DeviceCLI:
    """构造持有假（或缺失）设备服务的 DeviceCLI。"""
    return DeviceCLI(app=_app(service))


def _patch_input(monkeypatch, answers) -> None:
    """把 `builtins.input` 替换为依次吐出 answers 的队列（耗尽后返回空串）。"""
    queue = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(queue, ""))


# ── KV / info 辅助 ─────────────────────────────────────────────


def test_parse_kv_pairs():
    """输入 'a:1' 与 'b: two' → 输出 {'a':'1','b':'two'}（键值两端被 strip）。"""
    assert DeviceCLI._parse_kv_pairs("a:1", "b: two") == {"a": "1", "b": "two"}


def test_parse_kv_pairs_invalid_raises():
    """输入不含冒号的 'no-colon' → 期望抛 ValueError。"""
    with pytest.raises(ValueError):
        DeviceCLI._parse_kv_pairs("no-colon")


def test_parse_kv_pairs_only_splits_first_colon():
    """输入 'k:http://x' → 输出 {'k': 'http://x'}（只按第一个冒号切分）。"""
    assert DeviceCLI._parse_kv_pairs("k:http://x") == {"k": "http://x"}


def test_interactive_kv(monkeypatch):
    """输入多行 'key:value' 后接空行 → 输出对应字典。"""
    _patch_input(monkeypatch, ["a:1", "b: two words", ""])
    assert _cli()._interactive_kv() == {"a": "1", "b": "two words"}


def test_interactive_kv_skips_invalid_line(monkeypatch, capsys):
    """输入先来一行无冒号再给合法行 → 跳过无效行并输出提示，最终仅含合法键值。"""
    _patch_input(monkeypatch, ["oops", "a:1", ""])

    assert _cli()._interactive_kv() == {"a": "1"}
    assert "跳过无效行「oops」" in capsys.readouterr().out


# ── 设备规格采集与 info 合并 ───────────────────────────────────


@pytest.mark.parametrize(
    ("dtype", "answers", "expected"),
    [
        ("ssd", ["1", "5"], {"interface": "sata", "form_factor": "2280"}),
        ("hdd", ["7", ""], {"interface": "usb"}),
        ("tape", ["5"], {"generation": "lto5"}),
        ("tf_sd_card", [], {}),
        ("other", [], {}),
    ],
)
def test_collect_device_spec(monkeypatch, dtype, answers, expected):
    """输入设备类型 + 菜单应答 → 输出对应规格字典（回车/无需录入类型则输出 {}）。"""
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *a: next(it, ""))

    assert _collect_device_spec(dtype) == expected


def test_collect_device_spec_retries_invalid_code(monkeypatch, capsys):
    """输入非法编号再给合法编号 → 输出重试提示且只录入最终合法规格。"""
    _patch_input(monkeypatch, ["9", "1", "x", ""])

    assert _collect_device_spec("ssd") == {"interface": "sata"}
    assert "无效输入，请按菜单输入对应编号。" in capsys.readouterr().out


def test_merge_spec_info():
    """输入 (None|JSON 对象|非 JSON 文本, 规格) → 输出规范化 JSON 文本。"""
    spec = {"interface": "sata"}

    assert json.loads(_merge_spec_info(None, spec)) == spec
    assert json.loads(_merge_spec_info('{"note": "n"}', spec)) == {
        "note": "n",
        "interface": "sata",
    }

    with_note = json.loads(_merge_spec_info("plain text", spec))
    assert with_note["note"] == "plain text" and with_note["interface"] == "sata"

    non_dict = json.loads(_merge_spec_info("[1]", spec))
    assert non_dict["note"] == "[1]"


def test_print_info_diff(capsys):
    """输入新旧 info 且存在差异 → 输出表头 'key' 与全部键行。"""
    DeviceCLI._print_info_diff({"a": "1"}, {"a": "2", "b": "3"})

    out = capsys.readouterr().out
    assert "key" in out
    assert "a" in out and "b" in out


def test_print_info_diff_empty_prints_no_change(capsys):
    """输入两个空 info → 输出 'info 无变化。' 且不输出表头。"""
    DeviceCLI._print_info_diff({}, {})

    out = capsys.readouterr().out
    assert "info 无变化。" in out
    assert "key" not in out


# ── 服务可用性 ─────────────────────────────────────────────────


def test_missing_service_message(capsys):
    """输入 app=None → 输出 True 并打印“应用未初始化”。"""
    cli = DeviceCLI(app=None)

    assert cli._missing_service() is True
    assert "应用未初始化" in capsys.readouterr().out


def test_missing_service_when_service_absent(capsys):
    """输入 app 存在但 device_service=None → 输出 True 并打印“设备服务不可用”。"""
    assert _cli()._missing_service() is True
    assert "设备服务不可用" in capsys.readouterr().out


def test_commands_short_circuit_without_service(capsys):
    """输入 app=None 后调用 do_reg/do_list → 输出错误提示且不产生服务调用。"""
    cli = DeviceCLI(app=None)

    cli.do_reg("")
    cli.do_list("")

    assert capsys.readouterr().out.count("应用未初始化") == 2


# ── do_reg ─────────────────────────────────────────────────────


def test_do_reg_registers_and_merges_spec(monkeypatch, capsys):
    """输入名称/JSON info/序列号/类型 ssd/接口 2 → 输出登记成功，且 data 已合并规格。"""
    service = _FakeService(reg_device_manual="D1")
    _patch_input(monkeypatch, ["dev", '{"note": "x"}', "D1", "1", "2", ""])

    _cli(service).do_reg("")

    assert "成功登记设备: D1" in capsys.readouterr().out
    name, args, kwargs = service.calls[0]
    assert name == "reg_device_manual" and kwargs == {}
    data = args[0]
    assert data["serial"] == "D1"
    assert data["name"] == "dev"
    assert data["type"] == "ssd"
    assert json.loads(data["info"]) == {"note": "x", "interface": "sas"}


def test_do_reg_empty_optional_inputs_yield_none_and_empty_info(monkeypatch):
    """输入名称/info 留空、类型 1 → data 的 name/info 分别为 None 与 '{}'。"""
    service = _FakeService(reg_device_manual="D2")
    _patch_input(monkeypatch, ["", "", "D2", "1", ""])

    _cli(service).do_reg("")

    data = service.calls[0][1][0]
    assert data["name"] is None
    assert data["info"] == "{}"
    assert data["type"] == "ssd"


def test_do_reg_requires_serial(monkeypatch, capsys):
    """输入序列号留空 → 输出“序列号不能为空”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, ["", "", ""])

    _cli(service).do_reg("")

    assert "序列号不能为空" in capsys.readouterr().out
    assert service.calls == []


def test_do_reg_prints_error_on_service_exception(monkeypatch, capsys):
    """登记时服务抛异常 → 输出 '错误: ...' 而非崩溃。"""
    service = _FakeService(reg_device_manual=RuntimeError("重复序列号"))
    _patch_input(monkeypatch, ["", "", "D1", "1", ""])

    _cli(service).do_reg("")

    assert "错误: 重复序列号" in capsys.readouterr().out


# ── 查询 ───────────────────────────────────────────────────────


def test_do_list_prints_each_device():
    """输入 list → 输出 device_service 返回的每个设备。"""
    service = _FakeService(list_devices=["D1", "D2"])

    _cli(service).do_list("")

    assert service.calls[0][0] == "list_devices"


def test_do_get_with_target_loads_device(monkeypatch, capsys):
    """输入目标序列号 → 输出 '成功加载设备: ...'，并以该目标调用 load_device_by_target。"""
    service = _FakeService(load_device_by_target="DEV-D1")
    _patch_input(monkeypatch, ["D1"])

    _cli(service).do_get("")

    assert "成功加载设备: DEV-D1" in capsys.readouterr().out
    assert service.calls == [("load_device_by_target", ("D1",), {})]


def test_do_get_empty_target_falls_back_to_list(monkeypatch):
    """输入目标留空 → 期望退回 do_list（调用 list_devices 而非 load）。"""
    service = _FakeService(list_devices=[])
    _patch_input(monkeypatch, [""])

    _cli(service).do_get("")

    assert [call[0] for call in service.calls] == ["list_devices"]


# ── 字段更新 ───────────────────────────────────────────────────


def test_do_set_name_with_args(capsys):
    """输入 'D1 new' → 输出 '名称: old → new'，服务收到 ('D1','new')。"""
    service = _FakeService(set_name=("old", "new"))

    _cli(service).do_set_name("D1 new")

    assert "名称: old → new" in capsys.readouterr().out
    assert service.calls == [("set_name", ("D1", "new"), {})]


def test_do_set_name_interactive_rejects_empty(monkeypatch, capsys):
    """输入空参数后交互也留空 → 输出“序列号和新名称不能为空”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, ["D1", ""])

    _cli(service).do_set_name("")

    assert "序列号和新名称不能为空。" in capsys.readouterr().out
    assert service.calls == []


def test_do_set_state_prints_enum_values(monkeypatch, capsys):
    """输入 set_state D1 + 菜单编号 2 → 输出 '状态: unknown → healthy'。"""
    service = _FakeService(set_state=(DeviceState.UNKNOWN, DeviceState.HEALTHY))
    _patch_input(monkeypatch, ["2"])

    _cli(service).do_set_state("D1")

    assert "状态: unknown → healthy" in capsys.readouterr().out
    assert service.calls == [("set_state", ("D1", DeviceState.HEALTHY), {})]


def test_do_set_capacity_rejects_non_integer(capsys):
    """输入 'D1 abc' → 输出“容量必须为整数（字节）”，不调用服务。"""
    service = _FakeService()

    _cli(service).do_set_capacity("D1 abc")

    assert "容量必须为整数（字节）。" in capsys.readouterr().out
    assert service.calls == []


def test_do_set_capacity_passes_int(capsys):
    """输入 'D1 2048' → 服务收到整数 2048 并输出容量变更。"""
    service = _FakeService(set_capacity=(0, 2048))

    _cli(service).do_set_capacity("D1 2048")

    assert service.calls == [("set_capacity", ("D1", 2048), {})]
    assert "容量: 0 → 2048" in capsys.readouterr().out


def test_do_set_serial_prints_transition(capsys):
    """输入 'old new' → 输出 '序列号: old → new'。"""
    service = _FakeService(set_serial=("old", "new"))

    _cli(service).do_set_serial("old new")

    assert "序列号: old → new" in capsys.readouterr().out
    assert service.calls == [("set_serial", ("old", "new"), {})]


# ── info 操作 ──────────────────────────────────────────────────


def test_do_set_info_with_kv_args_calls_service(capsys):
    """输入 'D1 a:1 b:2' → 服务收到 {'a':'1','b':'2'} 并打印 info 对比表。"""
    service = _FakeService(set_info=({}, {"a": "1", "b": "2"}))

    _cli(service).do_set_info("D1 a:1 b:2")

    assert service.calls == [("set_info", ("D1", {"a": "1", "b": "2"}), {})]
    assert "key" in capsys.readouterr().out


def test_do_set_info_invalid_kv_prints_error(capsys):
    """输入 'D1 a:1 bad' → 输出解析错误原文，不调用服务。"""
    service = _FakeService()

    _cli(service).do_set_info("D1 a:1 bad")

    assert "无法解析「bad」" in capsys.readouterr().out
    assert service.calls == []


def test_do_append_info_uses_interactive_kv(monkeypatch):
    """输入参数不足 2 段（'D1'）+ 交互序列号与键值 → 服务收到 ('D1', 解析出的字典)。"""
    service = _FakeService(append_info=({}, {"n": "1"}))
    _patch_input(monkeypatch, ["D1", "n:1", ""])

    _cli(service).do_append_info("D1")

    assert service.calls == [("append_info", ("D1", {"n": "1"}), {})]


def test_do_delete_info_interactive_requires_key(monkeypatch, capsys):
    """输入 'D1' 后键名留空 → 输出“键名不能为空”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, [""])

    _cli(service).do_delete_info("D1")

    assert "键名不能为空。" in capsys.readouterr().out
    assert service.calls == []


def test_do_delete_info_with_key(capsys):
    """输入 'D1 note' → 服务收到 ('D1','note') 并打印 info 对比。"""
    service = _FakeService(delete_info=({"note": "x"}, {}), )

    _cli(service).do_delete_info("D1 note")

    assert service.calls == [("delete_info", ("D1", "note"), {})]
    assert "key" in capsys.readouterr().out


# ── 移除与返回 ─────────────────────────────────────────────────


def test_do_remove_prints_confirmation(capsys):
    """输入 'D1' → 输出 '已移除设备: D1'。"""
    service = _FakeService()

    _cli(service).do_remove("D1")

    assert "已移除设备: D1" in capsys.readouterr().out
    assert service.calls == [("remove_device", ("D1",), {})]


def test_do_remove_prints_error_on_exception(capsys):
    """移除时服务抛异常 → 输出 '错误: busy'。"""
    service = _FakeService(remove_device=RuntimeError("busy"))

    _cli(service).do_remove("D1")

    assert "错误: busy" in capsys.readouterr().out


def test_do_back_and_eof_return_true(capsys):
    """输入 back / EOF → 均返回 True（结束子命令循环），EOF 额外换行。"""
    cli = _cli()

    assert cli.do_back("") is True
    assert cli.do_EOF("") is True
    assert capsys.readouterr().out == "\n"
