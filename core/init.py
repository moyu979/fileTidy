# 本文件未经测试
import os
from core.conf.conf import init_conf
from core.log.init import init_log
from core.database.init import init_database
def init():
    path = "./database"
    if not os.path.exists(path):
        os.mkdir(path)

    init_conf()
    init_log()
    init_database()
