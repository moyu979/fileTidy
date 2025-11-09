"""核心主控流程。"""

import logging

from database.session import init_database
from utils.confs import init_conf_manager
from apis.restapi import start_rest_api


logger = logging.getLogger(__name__)


def init() -> None:
    """执行核心初始化流程。"""
    logger.info("开始初始化配置")
    init_conf_manager()

    logger.info("开始初始化数据库")
    init_database()

    logger.info("拉起rest api服务器")
    start_rest_api()