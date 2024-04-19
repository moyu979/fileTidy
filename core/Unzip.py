import sqlite3
import os
import sys

from _Hash import *
from _fileTime import *
from _Log import *
from _compareFile import *
from _removeFile import *
from _sizeManage import *

class Unzip:
    def __init__(self,db_path,unzip_files,storage_files) -> None:
        self.db_path=os.path.abspath(db_path).replace("\\","/")
        self.unzip_files=os.path.abspath(unzip_files).replace("\\","/")
        self.storage_files=os.path.abspath(storage_files).replace("\\","/")
        self.time=fileTime()

        Log.open(self.db_path)
        Log.writeLog(f"unzip --db {db_path} --unzip_files {unzip_files} --store {storage_files}")

        database=os.path.join(self.db_path,"files.db")
        self.conn=sqlite3.connect(database)
        self.cur=self.conn.cursor()

        self.unzip_datas=[]
        self.to_add_hash=[]

        self.sizes=sizeManage(self.unzip_files)

        self.run()

        self.conn.commit()
        self.conn.close()

        

    def run(self):
        paths=os.listdir(self.unzip_files)
        sizes=sizeManage(self.unzip_files)
        for i in paths:
            p=os.path.join(self.unzip_files,i)
            self.get_a_zip_pair(p)

    def get_a_zip_pair(self,path):
        files=os.listdir(path)
        zip_files=[]
        others=[]
        i:str
        for i in files:
            if i.endswith(".zip") or i.endswith(".rar") or i.endswith(".7z"):
                zip_files.append(i)
            else:
                others.append(i)
        hash_set=set()
        for i in zip_files:
            p=os.path.join(path,i)
            hash=getAHash(p)
            self.sizes.update(p)
            self.sizes.showProgress()
            hash_set.add(hash)

        all_hash=[]
        all=[]
        si=True
        for i in others:
            p=os.path.join(path,i)
            hashes=[]
            for root,dir,files in os.walk(path):
                for file in files:
                    pp=os.path.join(root,file)
                    hash=getAHash(pp)
                    hashes.append(hash)
                    if si:
                        all.append([hash,pp])
            hashes.sort()
            all_hash.append(hashes)

        if len(hash_set)!=1:
            Log.writeLog(f"[zip file error]\t{path}")
        elif not self.same(all_hash):
            Log.writeLog(f"[unzip file error]\t{path}")
        else:
            hash=list(hash_set)[0]
            self.write_db(path,hash,all)
            self.update_now()

    def write_db(self,parent_path,zip_hash,unzip_file):
        zip_storage=self.cur.execute("SELECT * FROM now WHERE hashMd5=?",(zip_hash,)).fetchall()
        if os.path.exists(zip_storage[0][2]):
            Log.writeLog(f"[warning] {zip_storage[0][2]} still exist")
        else:
            self.cur.execute("UPDATE now SET path=? where hashMd5=?",("removed",zip_hash))

        for i in unzip_file:
            self.cur.execute("INSERT INTO unzip VALUES (?,?,?,?,?,?) ",(self.time,zip_hash,0,i[0],0,i[1].replace(parent_path,"")))
            files=self.cur.execute("SELECT * FROM now WHERE hashMd5=?",(i[0],)).fetchall
            if len(files)!=0:
                Log.writeLog(f"[file already exists]\t{i[1]} with hash {i[1]}")
            else:
                self.to_add_hash.append(i)
    
    def update_now(self):
        to_match=self.storage_files+"%"
        exist_db_files=self.cur.execute("SELECT * FROM now WHERE path LIKE ?",(to_match,)).fetchall()
        files_loged={}
        for i in exist_db_files:
            files_loged[i[2]]=i

        not_exit=[]
        for root,dir,files in os.walk(self.storage_files):
            for file in files:
                path=os.path.join(root,file).replace("\\","/")
                if path in files_loged:
                    pass
                else:
                    not_exit.append(path)
        to_log={}
        for i in self.to_add_hash:
            to_log[i[0]]=i
        for i in not_exit:
            hash=getAHash(i)
            if hash not in to_log:
                Log.writeLog(f"[have not loged file] {i}")
            else:
                self.cur.execute("INSERT INTO NOW VALUES (?,?,?,?)",(self.time,hash,i,0))


        


    def same(self,files):
        count=len(files)
        number=len(files[0])
        for i in files:
            if len(i)!=number:
                return False
        for i in range(0,count):
            for j in range(number):
                if files[0][j]!=files[i][j]:
                    return False
                
        return True


