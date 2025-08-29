# 本文件未经测试
import os
from pathlib import Path
import sqlite3
import logging
import core.conf.conf as conf
logger = logging.getLogger(__name__)
# 用于新建数据库的函数
def init_database():
    path=conf.get("db_path")
    logger.info(f"初始化数据库，路径为{path}")
    if path is None:
        logging.error("初始化数据库的路径不能为空")
    elif os.path.exists(path):
        logging.debug(f"位于{path}的数据库已经存在，什么都不会做")
    else:
        script_dir = Path(__file__).resolve().parent
        script_path=os.path.join(script_dir,"init.sql")
        with open(script_path,"r") as script:
            sql_script=script.read()
        conn=sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.executescript(sql_script)
        conn.commit()
        conn.close()



