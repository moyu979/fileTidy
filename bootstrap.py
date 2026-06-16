import argparse
import logging

from application.app import App
from application.storage.device.factory import device_factory
from application.storage.device.service import device_service
from application.storage.file.file_service import file_service
from application.storage.super_device.factory import super_device_factory
from application.storage.super_device.service import super_device_service
from application.storage.super_volume.factory import super_volume_factory
from application.storage.super_volume.service import super_volume_service
from application.storage.volume.factory import volume_factory
from application.storage.volume.service import volume_service

from infra.config.config import Config
from infra.log.logger import setup_logging
from infra.operate_log.operate_log import setup_event_logger
from infra.persistence.database import build_session_factory
from infra.persistence.init_db import init_database
from infra.persistence.storage.device_repository import device_repository
from infra.persistence.storage.file_repository import file_repository
from infra.persistence.storage.super_device_repository import super_device_repository
from infra.persistence.storage.super_volume_repo import super_Volume_repository
from infra.persistence.storage.volume_repository import volume_repository
# volume 系统操作已改为直接函数调用，不再需要 adapter
from infra.system.storage.file.hash import file_hash

logger = logging.getLogger(__name__)

def bootstrap(args: argparse.Namespace):
    config = Config(args)

    session_factory, engine = build_session_factory(config["database"]["path"])
    init_database(engine, session_factory)

    setup_logging(config)
    setup_event_logger(config)
    logger.info("Bootstrap log completed")

    # 设备 —— 仓库保持类实例，系统操作改为直接函数调用
    device_repository_instance = device_repository(session_factory)
    device_service_instance = device_service(device_repository_instance)
    device_factory.set_device_repository(device_repository_instance)

    super_device_repository_instance = super_device_repository(session_factory)
    super_device_factory.set_device_repository(device_repository_instance)
    super_device_service_instance = super_device_service(super_device_repository_instance)

    file_repository_instance = file_repository(session_factory)
    file_hasher = file_hash(config)
    file_service_instance = file_service(file_repository_instance, file_hasher)

    volume_repository_instance = volume_repository(session_factory)
    volume_service_instance = volume_service(
        volume_repository_instance,
        file_service_instance,
        device_repository_instance,
        super_device_repository_instance,
    )

    super_volume_repository_instance = super_Volume_repository(session_factory)
    super_volume_factory.set_volume_repository(volume_repository_instance)
    super_volume_service_instance = super_volume_service(
        super_volume_repository_instance,
        volume_repository_instance,
    )

    app = App(
        device_service_instance,
        volume_service_instance,
        super_device_service_instance,
        super_volume_service_instance,
    )

    logger.info("app bootstrap completed")
    return app, config
    
