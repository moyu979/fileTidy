from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from application.app import App
from infra.config.config import Config


def create_app() -> FastAPI:
    return FastAPI(title="fileTidy")


def run_service(app: App | None, config: Config) -> None:
    """根据 ``restapi`` 配置中的 host/port 启动空 FastAPI 服务。"""
    _ = app
    rest = config["restapi"]
    host = str(rest["restapi_host"])
    port = int(rest["restapi_port"])
    web = create_app()
    uvicorn.run(web, host=host, port=port)
