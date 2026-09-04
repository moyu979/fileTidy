# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - FastAPI 服务 - RESTful API 路由定义

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from application.app import App
from infra.config.app_config import AppConfig


def create_app() -> FastAPI:
    """创建并返回一个 FastAPI 应用实例。

    Returns:
        配置了标题为 "fileTidy" 的 FastAPI 实例。
    """
    # TODO(P2): 当前 FastAPI 应用没有任何路由注册，需要添加 REST API 端点
    return FastAPI(title="fileTidy")


def run_service(app: App | None, config: Config) -> None:
    """根据 restapi 配置中的 host/port 启动 FastAPI 服务。

    Args:
        app: 应用实例（当前未使用）。
        config: 全局配置对象，需包含 restapi.restapi_host 和 restapi.restapi_port。
    """
    _ = app
    rest = config["restapi"]
    host = str(rest["restapi_host"])
    port = int(rest["restapi_port"])
    web = create_app()
    uvicorn.run(web, host=host, port=port)
