import sqlite3
import logging

from core.tools.confs import conf
from core.tools.confs import *


def db_execute(cmd):

    _,err=check_db_existance()
    if err is not None:
        return None,err
    
    conn=sqlite3.connect(get_db_path())
    cursor=conn.cursor()
    try:
        result=cursor.execute(cmd).fetchall()
    except Exception:
        conn.commit()
        conn.close()
        logging.error(f"execute line {cmd} error")
        return None,f"execute line {cmd} error"
    
    conn.commit()
    conn.close()
    return result,None

def check_db_existance():
    db_path=get_db_path()
    if not os.path.exists(db_path):
        logging.warning(f"data base path {db_path} not exist")
        return None,f"data base path {db_path} not exist"
    return None,None
    
def get_db_path():
    return os.path.join(conf["data_path"],conf["db_name"])
