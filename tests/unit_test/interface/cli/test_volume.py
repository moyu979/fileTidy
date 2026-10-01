# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：interface/cli/volume —— VolumeCLI 卷管理子命令。

目的：验证卷子命令的交互流程（`do_init` / `do_reg` / `do_register_volume_by_csv`）
与参数解析、info 对比打印、字段更新与移除等 `do_*` 对 `volume_service`
的调用契约，全部在假服务下进行，不接触真实数据库/文件系统。

输入：`builtins.input` 应答序列、命令行参数字符串、临时 CSV 文件、仅含
`volume_service` 的 app 替身。
期望输出：打印文本、传给 `volume_service` 的关键字参数与异常分支提示语。
"""

from __future__ import annotations

import types
from datetime import datetime
from pathlib import Path

import pytest

from domain.storage.volume.enum import VolumeState
from interface.cli.volume import VolumeCLI


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


def _cli(service=None) -> VolumeCLI:
    """构造持有假（或缺失）卷服务的 VolumeCLI。"""
    return VolumeCLI(app=types.SimpleNamespace(volume_service=service))


def _patch_input(monkeypatch, answers) -> None:
    """把 `builtins.input` 替换为依次吐出 answers 的队列（耗尽后返回空串）。"""
    queue = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(queue, ""))


def _write_csv(path: Path, header: str, row: str) -> Path:
    """写出只有一行数据的 CSV 并返回其路径。"""
    path.write_text(f"{header}\n{row}\n", encoding="utf-8")
    return path


# ── KV / info 辅助 ─────────────────────────────────────────────


def test_parse_kv_pairs():
    """输入 'a:1' 与 'b: two' → 输出 {'a':'1','b':'two'}。"""
    assert VolumeCLI._parse_kv_pairs("a:1", "b: two") == {"a": "1", "b": "two"}


def test_parse_kv_pairs_invalid_raises():
    """输入不含冒号的 'no-colon' → 期望抛 ValueError。"""
    with pytest.raises(ValueError):
        VolumeCLI._parse_kv_pairs("no-colon")


def test_interactive_kv(monkeypatch):
    """输入多行 'key:value' 后接空行 → 输出对应字典。"""
    _patch_input(monkeypatch, ["a:1", "b: two words", ""])

    assert _cli()._interactive_kv() == {"a": "1", "b": "two words"}


def test_print_info_diff(capsys):
    """输入新旧 info 且存在差异 → 输出表头 'key' 与全部键行。"""
    VolumeCLI._print_info_diff({"a": "1"}, {"a": "2", "b": "3"})

    out = capsys.readouterr().out
    assert "key" in out
    assert "a" in out and "b" in out


def test_print_info_diff_empty_prints_no_change(capsys):
    """输入两个空 info → 输出 'info 无变化。'。"""
    VolumeCLI._print_info_diff({}, {})

    assert "info 无变化。" in capsys.readouterr().out


# ── 服务可用性 ─────────────────────────────────────────────────


def test_missing_service_message(capsys):
    """输入 app=None → 输出 True 并打印“应用未初始化，无法执行卷操作”。"""
    cli = VolumeCLI(app=None)

    assert cli._missing_service() is True
    assert "应用未初始化" in capsys.readouterr().out


def test_missing_service_when_service_absent(capsys):
    """输入 app 存在但 volume_service=None → 输出 True 并打印“卷服务不可用”。"""
    assert _cli()._missing_service() is True
    assert "卷服务不可用" in capsys.readouterr().out


# ── 查询 ───────────────────────────────────────────────────────


def test_do_list_empty_prints_placeholder(capsys):
    """输入 list 且服务返回空列表 → 输出 '（无卷）'。"""
    _cli(_FakeService(list_volumes=[])).do_list("")

    assert "（无卷）" in capsys.readouterr().out


def test_do_list_prints_each_volume(capsys):
    """输入 list 且服务返回 2 个卷 → 两个卷字符串都被打印。"""
    _cli(_FakeService(list_volumes=["V1", "V2"])).do_list("")

    out = capsys.readouterr().out
    assert "V1" in out and "V2" in out


def test_do_get_empty_target_falls_back_to_list(monkeypatch):
    """输入序列号留空 → 期望退回 do_list（调用 list_volumes）。"""
    service = _FakeService(list_volumes=[])
    _patch_input(monkeypatch, [""])

    _cli(service).do_get("")

    assert [call[0] for call in service.calls] == ["list_volumes"]


def test_do_get_found_prints_volume(monkeypatch, capsys):
    """输入已知序列号 → 输出该卷内容，不输出“未找到”。"""
    service = _FakeService(get_volume="VOL-V1")
    _patch_input(monkeypatch, ["V1"])

    _cli(service).do_get("")

    out = capsys.readouterr().out
    assert "VOL-V1" in out and "未找到该卷" not in out
    assert service.calls == [("get_volume", ("V1",), {})]


def test_do_get_not_found_prints_message(monkeypatch, capsys):
    """输入未知序列号（服务返回 None）→ 输出 '未找到该卷。'。"""
    service = _FakeService(get_volume=None)
    _patch_input(monkeypatch, ["GHOST"])

    _cli(service).do_get("")

    assert "未找到该卷。" in capsys.readouterr().out


# ── do_init ────────────────────────────────────────────────────


def test_do_init_requires_path(monkeypatch, capsys):
    """输入挂载点留空 → 输出“路径不能为空”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, [""])

    _cli(service).do_init("")

    assert "错误: 路径不能为空。" in capsys.readouterr().out
    assert service.calls == []


def test_do_init_calls_init_volume_with_resolved_path(monkeypatch, capsys, tmp_path):
    """输入挂载点/名称/唯一挂载点/info → init_volume 收到 resolve 后的绝对路径。"""
    service = _FakeService(init_volume="VOL-NEW")
    _patch_input(monkeypatch, [str(tmp_path), "卷名", "ump-1", "a:1", ""])

    _cli(service).do_init("")

    assert "初始化成功: VOL-NEW" in capsys.readouterr().out
    assert service.calls == [
        (
            "init_volume",
            (),
            {
                "path": str(tmp_path.resolve()),
                "name": "卷名",
                "unique_mount_point": "ump-1",
                "info": {"a": "1"},
            },
        )
    ]


# ── do_reg ─────────────────────────────────────────────────────


def test_do_reg_manual_branch_calls_register_volume_by_info(monkeypatch, capsys):
    """输入路径留空的手动分支 → register_volume_by_info 收到全部手工字段。"""
    service = _FakeService(register_volume_by_info="VOL1")
    _patch_input(
        monkeypatch,
        ["", "", "", "note:hi", "", "V1", "D1", "1", "1000", "/mnt/v1"],
    )

    _cli(service).do_reg("")

    assert "登记成功: VOL1" in capsys.readouterr().out
    assert service.calls == [
        (
            "register_volume_by_info",
            (),
            {
                "serial": "V1",
                "device_id": "D1",
                "name": None,
                "file_system": "ntfs",
                "capacity": 1000,
                "unique_mount_point": None,
                "volume_path": "/mnt/v1",
                "info": {"note": "hi"},
            },
        )
    ]


def test_do_reg_manual_empty_device_id_defaults(monkeypatch):
    """手动分支中设备序列号留空 → device_id 默认 'EXTERNAL_DEVICE'。"""
    service = _FakeService(register_volume_by_info="VOL1")
    _patch_input(monkeypatch, ["", "", "", "", "V1", "", "1", "", ""])

    _cli(service).do_reg("")

    kwargs = service.calls[0][2]
    assert kwargs["device_id"] == "EXTERNAL_DEVICE"
    assert kwargs["capacity"] is None
    assert kwargs["volume_path"] is None


def test_do_reg_manual_requires_serial(monkeypatch, capsys):
    """手动分支中序列号留空 → 输出“序列号不能为空”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, ["", "", "", "", ""])

    _cli(service).do_reg("")

    assert "错误: 序列号不能为空。" in capsys.readouterr().out
    assert service.calls == []


def test_do_reg_manual_invalid_capacity_warns(monkeypatch, capsys):
    """手动分支中容量非整数 → 输出格式警告并把 capacity 置为 None。"""
    service = _FakeService(register_volume_by_info="VOL1")
    _patch_input(monkeypatch, ["", "", "", "", "V1", "D1", "1", "abc", ""])

    _cli(service).do_reg("")

    assert "警告: 容量格式不正确，将留空" in capsys.readouterr().out
    assert service.calls[0][2]["capacity"] is None


def test_do_reg_path_branch_calls_reg_volume(monkeypatch, capsys, tmp_path):
    """输入有效路径并确认登记 datas 文件 → reg_volume 收到 resolve 后的路径与 register_files=True。"""
    service = _FakeService(reg_volume="VOL2")
    _patch_input(monkeypatch, [str(tmp_path), "vol", "", "", "y"])

    _cli(service).do_reg("")

    assert "登记成功: VOL2" in capsys.readouterr().out
    assert service.calls == [
        (
            "reg_volume",
            (),
            {
                "path": str(tmp_path.resolve()),
                "name": "vol",
                "unique_mount_point": None,
                "info": {},
                "register_files": True,
            },
        )
    ]


def test_do_reg_path_branch_default_reg_files_false(monkeypatch, tmp_path):
    """输入有效路径但登记 datas 询问留空 → register_files=False。"""
    service = _FakeService(reg_volume="VOL2")
    _patch_input(monkeypatch, [str(tmp_path), "", "", "", ""])

    _cli(service).do_reg("")

    assert service.calls[0][2]["register_files"] is False


def test_do_reg_prints_error_on_service_exception(monkeypatch, capsys, tmp_path):
    """登记时服务抛异常 → 输出 '登记失败: ...' 而非崩溃。"""
    service = _FakeService(reg_volume=RuntimeError("卷已存在"))
    _patch_input(monkeypatch, [str(tmp_path), "", "", "", ""])

    _cli(service).do_reg("")

    assert "登记失败: 卷已存在" in capsys.readouterr().out


# ── do_register_volume_by_csv ──────────────────────────────────


def test_do_register_volume_by_csv_requires_csv_path(monkeypatch, capsys):
    """输入 CSV 路径留空 → 输出“CSV 文件路径不能为空”，不读取文件。"""
    service = _FakeService()
    _patch_input(monkeypatch, [""])

    _cli(service).do_register_volume_by_csv("")

    assert "错误: CSV 文件路径不能为空。" in capsys.readouterr().out
    assert service.calls == []


def test_do_register_volume_by_csv_reports_missing_columns(
    monkeypatch, capsys, tmp_path
):
    """输入列名不全的 CSV → 输出缺少必要列，不调用服务。"""
    csv_path = _write_csv(
        tmp_path / "bad.csv", "sha256,hash,size,path", "a,b,1,f"
    )
    service = _FakeService()
    _patch_input(monkeypatch, [str(csv_path), str(tmp_path), "", "", ""])

    _cli(service).do_register_volume_by_csv("")

    out = capsys.readouterr().out
    assert "CSV 缺少必要列" in out
    assert service.calls == []


def test_do_register_volume_by_csv_path_branch_calls_service(
    monkeypatch, capsys, tmp_path
):
    """输入含 sha512/hash/size/path 的 CSV 与卷路径 → register_volume_by_csv 被调用。"""
    csv_path = _write_csv(
        tmp_path / "good.csv", "sha512,hash,size,path", "s,h,1,f"
    )
    service = _FakeService(register_volume_by_csv="VOL3")
    _patch_input(monkeypatch, [str(csv_path), str(tmp_path), "vol", "", ""])

    _cli(service).do_register_volume_by_csv("")

    assert "登记成功: VOL3" in capsys.readouterr().out
    name, args, kwargs = service.calls[0]
    assert name == "register_volume_by_csv" and args == ()
    assert kwargs["path"] == str(tmp_path.resolve())
    assert kwargs["name"] == "vol"
    assert kwargs["info"] == {}
    assert list(kwargs["df"].columns) == ["sha512", "hash", "size", "path"]
    assert isinstance(kwargs["add_time"], datetime)


def test_do_register_volume_by_csv_manual_branch_calls_service(
    monkeypatch, tmp_path
):
    """卷路径留空（手动分支）→ register_volume_by_csv_data 收到手工字段。"""
    csv_path = _write_csv(
        tmp_path / "good.csv", "sha512,hash,size,path", "s,h,1,f"
    )
    service = _FakeService(register_volume_by_csv_data="VOL4")
    _patch_input(
        monkeypatch,
        [str(csv_path), "", "", "", "", "V4", "D4", "1", "500", "/root/v4"],
    )

    _cli(service).do_register_volume_by_csv("")

    name, args, kwargs = service.calls[0]
    assert name == "register_volume_by_csv_data" and args == ()
    assert kwargs["serial"] == "V4"
    assert kwargs["device_id"] == "D4"
    assert kwargs["file_system"] == "ntfs"
    assert kwargs["capacity"] == 500
    assert kwargs["volume_path"] == "/root/v4"


# ── 字段更新 / info / 移除 ─────────────────────────────────────


def test_do_set_name_prints_transition(capsys):
    """输入 'V1 new' → 服务收到 ('V1','new') 并输出 '名称: a → b'。"""
    service = _FakeService(set_name=("a", "b"))

    _cli(service).do_set_name("V1 new")

    assert service.calls == [("set_name", ("V1", "new"), {})]
    assert "名称: a → b" in capsys.readouterr().out


def test_do_set_name_interactive_rejects_empty(monkeypatch, capsys):
    """输入空参数后交互也留空 → 输出“序列号和新名称不能为空”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, ["V1", ""])

    _cli(service).do_set_name("")

    assert "序列号和新名称不能为空。" in capsys.readouterr().out
    assert service.calls == []


def test_do_set_device_id_prints_transition(capsys):
    """输入 'V1 D2' → 服务收到 ('V1','D2') 并输出 '所属设备: D1 → D2'。"""
    service = _FakeService(set_device_id=("D1", "D2"))

    _cli(service).do_set_device_id("V1 D2")

    assert service.calls == [("set_device_id", ("V1", "D2"), {})]
    assert "所属设备: D1 → D2" in capsys.readouterr().out


def test_do_set_capacity_rejects_non_integer(capsys):
    """输入 'V1 abc' → 输出“容量必须为整数（字节）”，不调用服务。"""
    service = _FakeService()

    _cli(service).do_set_capacity("V1 abc")

    assert "容量必须为整数（字节）。" in capsys.readouterr().out
    assert service.calls == []


def test_do_set_state_prints_enum_values(monkeypatch, capsys):
    """输入 set_state V1 + 菜单编号 2 → 输出 '状态: unknown → healthy'。"""
    service = _FakeService(set_state=(VolumeState.UNKNOWN, VolumeState.HEALTHY))
    _patch_input(monkeypatch, ["2"])

    _cli(service).do_set_state("V1")

    assert "状态: unknown → healthy" in capsys.readouterr().out
    assert service.calls == [("set_state", ("V1", VolumeState.HEALTHY), {})]


def test_do_set_serial_prints_transition(capsys):
    """输入 'old new' → 输出 '序列号: old → new'。"""
    service = _FakeService(set_serial=("old", "new"))

    _cli(service).do_set_serial("old new")

    assert "序列号: old → new" in capsys.readouterr().out


def test_do_set_info_with_kv_args_calls_service(capsys):
    """输入 'V1 a:1 b:2' → 服务收到 {'a':'1','b':'2'} 并打印 info 对比表。"""
    service = _FakeService(set_info=({}, {"a": "1", "b": "2"}))

    _cli(service).do_set_info("V1 a:1 b:2")

    assert service.calls == [("set_info", ("V1", {"a": "1", "b": "2"}), {})]
    assert "key" in capsys.readouterr().out


def test_do_delete_info_requires_key(monkeypatch, capsys):
    """输入 'V1' 后键名留空 → 输出“键名不能为空”，不调用服务。"""
    service = _FakeService()
    _patch_input(monkeypatch, [""])

    _cli(service).do_delete_info("V1")

    assert "键名不能为空。" in capsys.readouterr().out
    assert service.calls == []


def test_do_remove_prints_confirmation(capsys):
    """输入 'V1' → 输出 '已移除卷: V1'。"""
    service = _FakeService()

    _cli(service).do_remove("V1")

    assert "已移除卷: V1" in capsys.readouterr().out
    assert service.calls == [("remove_volume", ("V1",), {})]


def test_do_remove_prints_error_on_exception(capsys):
    """移除时服务抛异常 → 输出 '错误: 卷被占用'。"""
    service = _FakeService(remove_volume=RuntimeError("卷被占用"))

    _cli(service).do_remove("V1")

    assert "错误: 卷被占用" in capsys.readouterr().out


def test_do_back_and_eof_return_true(capsys):
    """输入 back / EOF → 均返回 True（结束子命令循环），EOF 额外换行。"""
    cli = _cli()

    assert cli.do_back("") is True
    assert cli.do_EOF("") is True
    assert capsys.readouterr().out == "\n"
