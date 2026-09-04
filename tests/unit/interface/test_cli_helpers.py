# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：interface/cli —— CLI 纯函数辅助。

目的：验证各子命令的 KV 参数解析、info 展示/合并、设备规格交互采集、
file CLI 的 --key value 解析与“服务缺失”提示。

输入：参数串 / key:value 文本 / input 应答序列。
期望输出：解析出的字典、合并后的 JSON 文本与打印内容。
"""

from __future__ import annotations

import json

import pytest

from interface.cli.device import DeviceCLI, _collect_device_spec, _merge_spec_info
from interface.cli.file import FileCLI
from interface.cli.super_device import SuperDeviceCLI
from interface.cli.super_volume import SuperVolumeCLI
from interface.cli.volume import VolumeCLI


@pytest.mark.parametrize("cls", [DeviceCLI, VolumeCLI, SuperDeviceCLI, SuperVolumeCLI])
def test_parse_kv_pairs(cls):
    """'a:1 b: two' → {'a':'1','b':'two'}。"""
    assert cls._parse_kv_pairs("a:1", "b: two") == {"a": "1", "b": "two"}


@pytest.mark.parametrize("cls", [DeviceCLI, VolumeCLI, SuperDeviceCLI, SuperVolumeCLI])
def test_parse_kv_pairs_invalid_raises(cls):
    """缺少冒号 → ValueError。"""
    with pytest.raises(ValueError):
        cls._parse_kv_pairs("no-colon")


@pytest.mark.parametrize("cls", [DeviceCLI, VolumeCLI, SuperDeviceCLI, SuperVolumeCLI])
def test_interactive_kv(monkeypatch, cls):
    """多行 key:value + 空行结束 → 字典。"""
    answers = iter(["a:1", "b: two words", ""])
    monkeypatch.setattr("builtins.input", lambda *a: next(answers))
    assert cls(app=None)._interactive_kv() == {"a": "1", "b": "two words"}


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
def test_collect_device_spec(monkeypatch, capsys, dtype, answers, expected):
    """不同设备类型按菜单交互 → 写入对应规格键。"""
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *a: next(it, ""))
    assert _collect_device_spec(dtype) == expected


def test_merge_spec_info():
    """info 合并：None/合法对象/非 JSON 文本 → 规范 JSON。"""
    spec = {"interface": "sata"}
    assert json.loads(_merge_spec_info(None, spec)) == spec
    merged = json.loads(_merge_spec_info('{"note": "n"}', spec))
    assert merged == {"note": "n", "interface": "sata"}
    with_note = json.loads(_merge_spec_info("plain text", spec))
    assert with_note["note"] == "plain text"
    assert with_note["interface"] == "sata"
    non_dict = json.loads(_merge_spec_info("[1]", spec))
    assert non_dict["note"] == "[1]"


def test_print_info_diff(capsys):
    """新旧 info 不同 → 打印表头与键行。"""
    VolumeCLI._print_info_diff({"a": "1"}, {"a": "2", "b": "3"})
    out = capsys.readouterr().out
    assert "key" in out
    assert "a" in out and "b" in out


def test_file_cli_parse_args():
    """--key value 风格解析，含无值 flag。"""
    cli = FileCLI(app=None)
    assert cli._parse_args("--src a --dst b --force") == {
        "src": "a", "dst": "b", "force": "",
    }


def test_device_cli_missing_service_message(capsys):
    """app 为 None → 打印“应用未初始化”。"""
    cli = DeviceCLI(app=None)
    assert cli._missing_service() is True
    assert "应用未初始化" in capsys.readouterr().out
