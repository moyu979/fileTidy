import logging
import os
import sqlite3
from core.tools.db_tools import get_db_path
from core.tools.process import ProcessManage
from core.tools.hash import get_hash
class check_file:
    def __init__(self):
        """
        mode0:严丝合缝的检查，不管是文件有多还是记录有多都不行
        mode1:只要数据库里的文件都在就行
        mode2:只要文件都在数据库里就行
        """
        self.mode=0

        self.check_path=""
        self.check_volume=""

        self.more_file=False
        self.more_log=False

    def check(self):
        pass

    def execute(self):
        self.conn=sqlite3.connect(get_db_path())
        self.cursor=self.conn.cursor()

        if self.check_volume=="":
            datas_search=self.cursor.execute("SELECT md5 FROM files").fetchall()
        else:
            datas_search=self.cursor.execute("SELECT md5 FROM files WHERE storage=?",(self.check_volume,)).fetchall()
        datas=[]

        for i in datas_search:
            datas.append(i[0])

        process_manage=ProcessManage(self.check_path)

        file_hash=[]

        for root,dirs,files in os.walk(self.check_path):
            for file in files:
                p=os.path.join(root,file)
                file_hash.append(get_hash(p))
                process_manage.update(p)

        for i in file_hash:
            if i in datas:
                datas.remove(i)
            else:
                print(i)
                self.more_file=True

        if len(datas)!=0:
            print(datas)
            self.more_log=True
        print()
        logging.debug(f"has unloged file:{self.more_file}")
        logging.debug(f"has no file log:{self.more_log}")
        if self.mode=="0":
            return self.more_file and self.more_log
        elif self.mode=="1":
            return self.more_log
        elif self.mode=="2":
            return self.more_file
        else:
            raise Exception("unknown check file mode")


                

        