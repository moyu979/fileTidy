# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：interface/fastapi/service —— FastAPI 服务装配。

目的：验证 `create_app()` 的实例化与路由表现状（源码标注 TODO(P2)：当前无任何
业务路由注册），以及 `run_service()` 从 config 读取 host/port、装配 FastAPI
实例后交给 uvicorn 启动的契约。真实启动 uvicorn（阻塞）会挂住测试，因此对
`uvicorn.run` 打桩，仅检查传入参数。

输入：无（`create_app`）／假 config 映射与假 app（`run_service`）。
期望输出：FastAPI 实例（标题 fileTidy、仅含文档路由、能产出 openapi 文档）；
uvicorn.run 收到 host 字符串、port 整数与 FastAPI 实例。
"""

from __future__ import annotations

import fastapi

import interface.fastapi.service as service_mod
from interface.fastapi.service import create_app, run_service

# FastAPI 默认自带的文档/规范路由；除此之外不应有任何业务路由。
_DEFAULT_ROUTE_PATHS = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


def _uvicorn_recorder(monkeypatch):
    """把 `uvicorn.run` 换成记录器并返回记录列表。"""
    calls: list[dict] = []

    def fake_run(web, host=None, port=None, **kwargs):
        calls.append({"web": web, "host": host, "port": port, "kwargs": kwargs})

    monkeypatch.setattr(service_mod.uvicorn, "run", fake_run)
    return calls


# ── 可导入性 ───────────────────────────────────────────────────


def test_module_exposes_factory_and_runner():
    """输入模块导入结果 → 期望 create_app 与 run_service 均为可调用对象。"""
    assert callable(service_mod.create_app)
    assert callable(service_mod.run_service)


# ── create_app ─────────────────────────────────────────────────


def test_create_app_returns_fastapi_with_title():
    """输入无 → 期望返回 FastAPI 实例且标题为 'fileTidy'。"""
    app = create_app()

    assert isinstance(app, fastapi.FastAPI)
    assert app.title == "fileTidy"


def test_create_app_registers_no_business_routes():
    """输入无 → 期望路由表仅含 FastAPI 默认文档路由（源码 TODO(P2)：业务路由未实现）。"""
    paths = {route.path for route in create_app().routes}

    assert paths == _DEFAULT_ROUTE_PATHS


def test_create_app_openapi_document_is_servable():
    """输入无 → 期望能生成 openapi 文档（标题一致），无需启动网络服务。"""
    schema = create_app().openapi()

    assert schema["info"]["title"] == "fileTidy"
    assert schema["paths"] == {}


def test_create_app_returns_independent_instances():
    """输入无（连续两次调用）→ 期望得到两个互不相同的实例。"""
    assert create_app() is not create_app()


# ── run_service ────────────────────────────────────────────────


def test_run_service_passes_host_and_port_to_uvicorn(monkeypatch):
    """输入 config.restapi 与假 app → 期望 uvicorn.run 收到 host 字符串与 int(port)。"""
    calls = _uvicorn_recorder(monkeypatch)
    config = {"restapi": {"restapi_host": "127.0.0.1", "restapi_port": "8123"}}

    run_service(app=None, config=config)

    assert len(calls) == 1
    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["port"] == 8123
    assert isinstance(calls[0]["port"], int)


def test_run_service_serves_freshly_created_app(monkeypatch):
    """输入 config 与假 app → 期望传入 uvicorn 的是 create_app() 产物（标题 fileTidy）。"""
    calls = _uvicorn_recorder(monkeypatch)
    config = {"restapi": {"restapi_host": "0.0.0.0", "restapi_port": 5001}}

    run_service(app="APP", config=config)

    web = calls[0]["web"]
    assert isinstance(web, fastapi.FastAPI)
    assert web.title == "fileTidy"


def test_run_service_ignores_app_argument(monkeypatch):
    """输入同一 config、app 分别为 None 与哨兵对象 → 期望 uvicorn 调用参数完全一致。"""
    calls = _uvicorn_recorder(monkeypatch)
    config = {"restapi": {"restapi_host": "0.0.0.0", "restapi_port": 5001}}

    run_service(app=None, config=config)
    run_service(app=object(), config=config)

    assert len(calls) == 2
    assert calls[0]["host"] == calls[1]["host"] == "0.0.0.0"
    assert calls[0]["port"] == calls[1]["port"] == 5001


def test_run_service_requires_restapi_section(monkeypatch):
    """输入缺少 restapi 段的 config → 期望抛 KeyError 且不调用 uvicorn.run。"""
    calls = _uvicorn_recorder(monkeypatch)

    try:
        run_service(app=None, config={})
    except KeyError:
        pass
    else:  # pragma: no cover - 仅在契约被破坏时执行
        raise AssertionError("缺少 restapi 段时应抛 KeyError")

    assert calls == []
