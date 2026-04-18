import os
import shutil

from apps.common.config.config import init_config_manager
from apps.common.config.globalVars import CONFIG_PATH, LOG_PATH, WORKSPACE_PATH, DEFAULT_CONFIG_FILE, FILE_LOG_PATH
from apps.common.database.session import init_database
from apps.common.log.logger import Logger as logger
from apps.common.log.logger import init_log
from apps.common.log.file_logger import init_file_log

def init_file():
    if not os.path.exists(WORKSPACE_PATH):
        os.makedirs(WORKSPACE_PATH)
    if not os.path.exists(CONFIG_PATH):
        # 使用全局定义的资源文件路径，避免相对路径拼接
        shutil.copy(DEFAULT_CONFIG_FILE, CONFIG_PATH)
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)
    if not os.path.exists(FILE_LOG_PATH):
        os.makedirs(FILE_LOG_PATH)

def init():
    init_file()
    init_config_manager()
    init_log()
    init_file_log()
    init_database()
    logger.info("初始化完成")
