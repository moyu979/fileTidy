"""func_test 公共夹具：临时 SQLite、仓储、真实 App 与事件日志。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from application.app import App
from application.storage.device.service import DeviceService
from application.storage.super_device.service import SuperDeviceService
from application.storage.super_volume.service import SuperVolumeService
from application.storage.volume.service import VolumeService
from infra.operation_log.operation_log import setup_event_logger
from infra.persistence.database import build_session_factory
from infra.persistence.init_db import init_database
from infra.persistence.models import Base
from infra.persistence.storage.device_repository import DeviceRepository
from infra.persistence.storage.file_repository import FileRepository
from infra.persistence.storage.super_device_repository import SuperDeviceRepository
from infra.persistence.storage.super_volume_repository import SuperVolumeRepository
from infra.persistence.storage.volume_repository import VolumeRepository


class _LogConfig:
    """只暴露 log.operation_log_path 的最小配置替身。"""

    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir

    def __getitem__(self, key):
        assert key == "log"
        return {"operation_log_path": str(self.log_dir)}


class _NoopFileService:
    """功能测试用无副作用 FileService 替身（不注册文件、不哈希）。"""

    def register_folder(self, *args, **kwargs):
        return []

    def register_by_csv(self, *args, **kwargs):
        return []


@pytest.fixture
def session_factory(tmp_path):
    """空库（仅建表）的会话工厂。"""
    engine_factory, engine = build_session_factory(f"sqlite:///{tmp_path / 'app.db'}")
    Base.metadata.create_all(bind=engine)
    yield engine_factory
    engine.dispose()


@pytest.fixture
def seeded_session_factory(tmp_path):
    """按真实启动流程建表并填充默认占位数据的会话工厂。"""
    engine_factory, engine = build_session_factory(f"sqlite:///{tmp_path / 'app.db'}")
    init_database(engine, engine_factory)
    yield engine_factory
    engine.dispose()


@pytest.fixture
def repos(session_factory):
    """返回全部真实仓储实例（共享一个会话工厂）。"""
    return {
        "device": DeviceRepository(session_factory),
        "volume": VolumeRepository(session_factory),
        "super_device": SuperDeviceRepository(session_factory),
        "super_volume": SuperVolumeRepository(session_factory),
        "file": FileRepository(session_factory),
        "session_factory": session_factory,
    }


@pytest.fixture
def event_log_dir(tmp_path, monkeypatch):
    """把全局事件日志指向临时目录，测试后复位。"""
    import infra.operation_log.operation_log as oplog

    log_dir = tmp_path / "operation_log"
    monkeypatch.setattr(oplog, "_logger", None)
    setup_event_logger(_LogConfig(log_dir))
    yield log_dir
    monkeypatch.setattr(oplog, "_logger", None)


@pytest.fixture
def full_app(repos, event_log_dir):
    """真实仓储 + 真实服务组装出的 App（file 服务为 no-op 替身）。"""
    device_service = DeviceService(repos["device"])
    super_device_service = SuperDeviceService(
        repos["super_device"], device_repository=repos["device"]
    )
    volume_service = VolumeService(
        volume_repository=repos["volume"],
        file_svc=_NoopFileService(),
        device_repository=repos["device"],
        super_device_repository=repos["super_device"],
    )
    super_volume_service = SuperVolumeService(
        repos["super_volume"], volume_repository=repos["volume"]
    )
    file_service = _NoopFileService()
    return App(
        device_service=device_service,
        volume_service=volume_service,
        super_device_service=super_device_service,
        super_volume_service=super_volume_service,
        file_service=file_service,
    )


@pytest.fixture
def patch_input(monkeypatch):
    """按顺序应答 input()，用尽后抛 AssertionError 防止静默死循环。"""

    def _patch(values: list[str]) -> None:
        queue = list(values)

        def fake_input(prompt=""):
            if not queue:
                raise AssertionError(f"input() 应答耗尽，仍有提示: {prompt}")
            return queue.pop(0)

        monkeypatch.setattr("builtins.input", fake_input)

    return _patch
