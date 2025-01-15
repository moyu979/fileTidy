from pathlib import Path
import sqlite3
import os
import logging

from core.tools.confs import conf

def init_db(path=None):
    data_storage_path=conf["data_path"]
    if not os.path.exists(data_storage_path):
        logging.info(f"creating {data_storage_path}")
        os.mkdir(data_storage_path)

    db_path=os.path.join(data_storage_path,conf["db_name"])
    if os.path.exists(db_path):
        logging.warning("data base already exists, nothing will be done")
    else:
        logging.info(f"init database in {db_path}")
        parent_dir = Path(__file__).resolve().parent.parent
        sql_dir=os.path.join(parent_dir,"resource")
        sql_file=os.path.join(sql_dir,"Init.sql")
        with open(sql_file,"r") as script:
            sql_script=script.read()
        conn=sqlite3.connect(db_path)
        cursor=conn.cursor()
        cursor.executescript(sql_script)
        conn.commit()
        conn.close()
