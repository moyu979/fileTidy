import os
from pathlib import Path
import sqlite3

import DataBase_pb2
from func import vars

def initDatabase(request,context):
    #初始化结果变量
    result=DataBase_pb2.InitResult()
    #如果不存在的话使用默认值
    if request.DataBasePath=="":
        request.DataBasePath="./DataBase"
    #初始化全部路径
    vars.data["db_path"]=request.DataBasePath
    if not os.path.exists(request.DataBasePath):
        os.mkdir(request.DataBasePath)
    db_path=os.path.join(vars.data["db_path"],"files.db")
    if os.path.exists(db_path):
        result.result="dataBaseAlreadyExist"
        return result
    #载入初始化脚本
    script_dir = Path(__file__).resolve().parent
    script_path=os.path.join(script_dir,"Init.sql")
    with open("./func/init.sql","r") as script:
        sql_script=script.read()
    #执行初始化
    conn=sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()

    result.result="success"
    result.info=f"init database in \"{vars.data["db_path"]}\""

    return result

