# 本文件未经测试
import os
import sys
import logging
from core.conf.conf import get, init_conf
from core.log.init import init_log
from core.database.init import init_database
from core.storage.storage_factory import StorageFactory
from core.env_check import check_dependencies

logger = logging.getLogger(__name__)

def init():
    path = "./data"
    if not os.path.exists(path):
        os.mkdir(path)

    init_conf()
    init_log()
    success, results = check_dependencies()
    if not success:
        # 只有当 all_env_fail 为 false 时才退出程序
        if not get("all_env_fail"):
            sys.exit(1)
        else:
            print("111")
            logger.warning("在部分依赖缺失的情况下继续执行（all_env_fail=True），可能会导致部分功能不可用")
    
    init_database()
    StorageFactory.init_storage()
