"""功能测试：CLI 命令的真实登记/查询/删除流程。

目的：通过真实 App（真实仓储/服务）驱动各子命令 do_*，验证界面层输入
解析、服务调用、成功/错误输出与数据库落库的端到端行为。

输入：patch_input 提供的应答队列。
期望输出：命令打印与 DB 状态符合预期；占用保护在 CLI 层表现为错误信息。
"""

from __future__ import annotations

import json

from interface.cli.device import DeviceCLI
from interface.cli.super_device import SuperDeviceCLI
from interface.cli.super_volume import SuperVolumeCLI
from interface.cli.volume import VolumeCLI


def _device_cli(full_app):
    return DeviceCLI(app=full_app)


def _super_device_cli(full_app):
    return SuperDeviceCLI(app=full_app)


def _volume_cli(full_app):
    return VolumeCLI(app=full_app)


def _super_volume_cli(full_app):
    return SuperVolumeCLI(app=full_app)


def test_cli_register_chain_query_and_remove(full_app, patch_input, capsys):
    """登记设备→超级设备→卷→超级卷，再逐级查询与删除。"""
    # 1. 登记设备 CLI-D1（ssd，不填规格）
    patch_input(["CLI 设备", "", "CLI-D1", "1", ""])
    _device_cli(full_app).do_reg("")
    out = capsys.readouterr().out
    assert "成功登记设备: CLI-D1" in out
    assert full_app.device_service.load_device(serial="CLI-D1") is not None

    # 2. 登记单盘超级设备 CLI-SD1
    patch_input(["CLI-SD1", "", "1", "", "y", "CLI-D1", ""])
    _super_device_cli(full_app).do_reg("")
    out = capsys.readouterr().out
    assert "成功登记超级设备: CLI-SD1" in out

    # 3. 手动登记卷 CLI-V1（走“卷路径留空 → 自动探测输入”分支）
    patch_input([
        "",                    # 卷路径（留空=手动）
        "",                    # 卷名
        "",                    # unique_mount_point
        "note:hello",          # info 键值
        "",                    # info 结束
        "CLI-V1",              # serial
        "CLI-D1",              # device_id
        "1",                   # 卷类型 ntfs
        "",                    # 容量
        "",                    # volume_path（留空触发 get_path）
        "/mnt/cli-v1",         # get_path 的应答
    ])
    _volume_cli(full_app).do_reg("")
    out = capsys.readouterr().out
    assert "登记成功" in out
    vol = full_app.volume_service.get_volume("CLI-V1")
    assert vol is not None
    assert json.loads(vol)["serial"] == "CLI-V1"
    assert json.loads(vol)["device_id"] == "CLI-D1"

    # 4. 登记超级卷 CLI-SV1（copy，成员 CLI-V1）
    patch_input(["", "1", "", "CLI-V1", ""])
    _super_volume_cli(full_app).do_reg("")
    out = capsys.readouterr().out
    assert "成功登记超级卷" in out
    sv_serial = json.loads(out.rsplit("成功登记超级卷: ", 1)[1].strip())["serial"]
    assert full_app.super_volume_service.get_super_volume(sv_serial) is not None

    # 5. do_get 查询卷
    patch_input(["CLI-V1"])
    _volume_cli(full_app).do_get("")
    out = capsys.readouterr().out
    assert "CLI-V1" in out
    assert "未找到该卷" not in out

    # 6. 删除占用保护：卷仍属超级卷 → 错误输出
    _volume_cli(full_app).do_remove("CLI-V1")
    out = capsys.readouterr().out
    assert "错误" in out
    assert "CLI-V1" in out

    # 7. 逐级删除
    _super_volume_cli(full_app).do_remove(sv_serial)
    assert f"已移除超级卷: {sv_serial}" in capsys.readouterr().out
    _volume_cli(full_app).do_remove("CLI-V1")
    assert "已移除卷: CLI-V1" in capsys.readouterr().out
    _super_device_cli(full_app).do_remove("CLI-SD1")
    assert "已移除超级设备: CLI-SD1" in capsys.readouterr().out

    # 8. 设备仍被超级设备结构 USING 占用 → 先摘除再删除
    _device_cli(full_app).do_remove("CLI-D1")
    assert "错误" in capsys.readouterr().out
    _super_device_cli(full_app).do_remove_device("CLI-SD1 CLI-D1")
    assert "子设备 CLI-D1 已从超级设备 CLI-SD1 移除" in capsys.readouterr().out
    _device_cli(full_app).do_remove("CLI-D1")
    assert "已移除设备: CLI-D1" in capsys.readouterr().out


def test_cli_register_unknown_volume_device_prints_error(full_app, patch_input, capsys):
    """登记卷时引用未登记设备 → CLI 打印登记失败而非崩溃。"""
    patch_input([
        "", "name", "", "", "CLI-VX", "GHOST-DEVICE", "1", "", "", "/tmp/x",
    ])
    _volume_cli(full_app).do_reg("")
    assert "登记失败" in capsys.readouterr().out
    assert full_app.volume_service.get_volume("CLI-VX") is None


def test_super_device_reg_without_devices_prints_error(full_app, patch_input, capsys):
    """登记超级设备时设备列表为空 → 打印友好错误，不抛 AssertionError。"""
    patch_input(["", "", "1", "", "y", ""])
    _super_device_cli(full_app).do_reg("")
    out = capsys.readouterr().out
    assert "至少需要一个设备" in out
    assert full_app.super_device_service.list_super_devices() == []
