import os
from pathlib import Path
import sqlite3
import logging
import platform

import init_setting.conf as conf
def init_database(path=None):
    if path is None:
        logging.info("No path provided, using default path")
        conf.set("path","./DataBase")
    else:
        conf.set("path",path)
        logging.info(f"Using provided path: {path}")

    path=conf.get("path")

    if not os.path.exists(path):
        os.mkdir(path)

    conf.set("db_path",os.path.join(path, "files.db"))
    if os.path.exists(conf.get("db_path")):
        logging.warning("Database already exists, skipping initialization")
        return
    
    script_dir = Path(__file__).resolve().parent
    script_path=os.path.join(script_dir,"Init.sql")
    with open(script_path, "r", encoding="utf-8") as script:
        sql_script=script.read()

    
    conn=sqlite3.connect(conf.get("db_path"))
    cursor = conn.cursor()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    logging.info(f"init database in \"{path}\"")

    conf.set("platform",platform.system())