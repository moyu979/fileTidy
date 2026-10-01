# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：application/app —— App 依赖注入容器。

目的：验证 App 作为应用唯一的装配根节点，能按约定持有 5 个服务实例
（device / volume / super_device / super_volume / file）；不复制、不转换、
不互相覆盖；初始化时向 `application.app` logger 输出一条 "App initialized"。

输入：5 个互不相同的哨兵对象、全部为 None 的服务、关键字参数、参数不足的调用。
期望输出：属性 identity 与传入对象一致；日志文本为 "App initialized"；
参数不足时抛 TypeError。
"""

from __future__ import annotations

import logging

import pytest

from application.app import App


def _sentinels():
    """返回 5 个互不相同的哨兵对象，用于验证 identity 而非相等性。"""
    return (object(), object(), object(), object(), object())


def test_stores_services_in_positional_order():
    """按位置传入 5 个不同对象 → 各属性分别指向对应的那一个对象。"""
    device, volume, super_device, super_volume, file = _sentinels()

    app = App(device, volume, super_device, super_volume, file)

    assert app.device_service is device
    assert app.volume_service is volume
    assert app.super_device_service is super_device
    assert app.super_volume_service is super_volume
    assert app.file_service is file


def test_accepts_keyword_arguments():
    """以关键字传入 5 个对象 → 关键字名与属性名一一对应。"""
    device, volume, super_device, super_volume, file = _sentinels()

    app = App(
        device_service=device,
        volume_service=volume,
        super_device_service=super_device,
        super_volume_service=super_volume,
        file_service=file,
    )

    assert app.device_service is device
    assert app.volume_service is volume
    assert app.super_device_service is super_device
    assert app.super_volume_service is super_volume
    assert app.file_service is file


def test_accepts_all_none_services():
    """5 个参数均为 None → 属性全为 None，构造不报错。"""
    app = App(None, None, None, None, None)

    assert app.device_service is None
    assert app.volume_service is None
    assert app.super_device_service is None
    assert app.super_volume_service is None
    assert app.file_service is None


def test_logs_initialized(caplog):
    """构造 App → `application.app` logger 记录一条 "App initialized"。"""
    with caplog.at_level(logging.INFO, logger="application.app"):
        App(*_sentinels())

    assert "App initialized" in [record.getMessage() for record in caplog.records]


def test_services_are_not_copied_or_wrapped():
    """传入可变服务对象 → 属性就是原对象（可原地被外部修改并可见）。"""
    service = {"tag": "origin"}

    app = App(service, service, service, service, service)
    app.device_service["tag"] = "changed"

    assert app.volume_service["tag"] == "changed"


@pytest.mark.parametrize("provided", [0, 1, 4])
def test_missing_arguments_raise_typeerror(provided):
    """服务参数不足（只传 provided 个）→ TypeError。"""
    with pytest.raises(TypeError):
        App(*_sentinels()[:provided])
