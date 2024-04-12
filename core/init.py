import sqlite3
import os

from _Log import *
cmd1=[
    '''CREATE TABLE now(
        time        txt,
        hashMd5     txt,
        path        txt,
        conflictNum INT DEFAULT 0
        )''',

    '''CREATE TABLE origin(
        time        txt,
        hashMd5     txt,
        path        txt,
        conflictNum INT DEFAULT 0
        )''',    

    '''CREATE TABLE unzip(
        time                txt,
        zipFileHashMd5      txt,
        zipFilePath         txt,
        zipFileConflictNum  INT DEFAULT 0,
        unzipFilehash       txt,
        unzipFileconf       txt,
        unzipName           txt
        
        )''',

    '''CREATE TABLE zip(
        time                txt,
        zipFileHashMd5      txt,
        zipFilePath         txt,
        zipFileConflictNum  INT DEFAULT 0,
        unzipFilehash       txt,
        unzipFileconf       txt,
        unzipName           txt
        )'''

]

class Init:
    def __init__(self,path):
        if not os.path.exists(path):
            os.mkdir(path)
        Log.open(path)
        Log.writeLog(f"init path={path}")
        db_path=os.path.join(path,"files.db")
        if os.path.exists(db_path):
            Log.writeLog(f"already exists dest database in {db_path}")
            return
        conn=sqlite3.connect(db_path)
        cur=conn.cursor()
        for i in cmd1:
            cur.execute(i)
        
        conn.commit()
        conn.close()
        Log.closeLog()

        
