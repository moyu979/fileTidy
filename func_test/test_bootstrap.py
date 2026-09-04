"""功能测试：bootstrap() 完整接线。

目的：按真实启动流程（pre_setup + bootstrap）验证配置、日志、数据库、
五个仓储/服务与 App 全部组装成功，默认数据与一次业务写读可用。

输入：临时 data_dir + assets 默认资源。
期望输出：返回 (App, AppConfig)，服务可执行、数据库落盘、事件日志可用。
"""

from __future__ import annotations

import argparse
import logging

import pytest

from application.app import App
from bootstrap import bootstrap
from infra.operation_log.operation_log import load_events
from infra.pre_setup import pre_setup


def test_bootstrap_wires_app_and_services(tmp_path, monkeypatch):
    """pre_setup + bootstrap → App/服务/配置/数据库全部就绪。"""
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)

    import infra.operation_log.operation_log as oplog

    monkeypatch.setattr(oplog, "_logger", None)

    data_dir = tmp_path / "datas"
    args = argparse.Namespace(data_dir=data_dir, modes=["cli"])
    pre_setup(args)

    app, config = bootstrap(args)
    try:
        # 组装结果
        assert isinstance(app, App)
        for name in (
            "device_service",
            "volume_service",
            "super_device_service",
            "super_volume_service",
            "file_service",
        ):
            assert getattr(app, name) is not None

        # 配置与数据库
        assert config["database"]["path"] == f"sqlite:///{data_dir}/database.db"
        assert config["restapi"]["restapi_port"] == 5001
        assert (data_dir / "database.db").is_file()

        # 默认占位数据 + 一次真实业务写读
        assert app.device_service.load_device(serial="EXTERNAL_DEVICE") is not None
        serial = app.device_service.reg_device_manual({
            "serial": "BOOT-D1",
            "name": "bootstrap 设备",
            "type": "ssd",
        })
        assert app.device_service.load_device(serial=serial) is not None

        # 事件日志已接线：刚才的登记应留下记录
        types = [r["type"] for r in load_events()]
        assert "DeviceRegistered" in types
    finally:
        config.stop_auto_reload()
        config.watcher.stop()
        added = [h for h in root_logger.handlers if h not in original_handlers]
        for handler in added:
            root_logger.removeHandler(handler)
            handler.close()
        monkeypatch.setattr(oplog, "_logger", None)
