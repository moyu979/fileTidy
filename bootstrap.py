import argparse
from zipapp import create_archive
from application.app import App
from infra.config.config import Config
from infra.log.logger import setup_logging
from infra.persistence.database import build_session_factory
from infra.persistence.init_db import init_database
from infra.persistence.storage.device_repository import device_repository
from application.storage.device.device_service import device_service
from infra.operate_log.operate_log import init_event_logger

import logging

logger = logging.getLogger(__name__)

def bootstrap(args: argparse.Namespace):
    config = Config(args)

    session_factory, engine = build_session_factory(config["database"]["path"])
    init_database(engine, session_factory)
    setup_logging(config)
    logger.info("Bootstrap log completed")
    device_repository_instance = device_repository(session_factory)
    device_service_instance = device_service(device_repository_instance)
    app = App(device_service_instance)
    init_event_logger(config)
    logger.info("app bootstrap completed")
    return app,config
    
