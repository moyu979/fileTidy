import sqlite3
import os
import sys

from _hash import *
from _fileTime import *
from _Log import *
from _compareFile import *
from _removeFile import *

class Add:
    def __init__(self,db_path,file_path,write_origin,check_exist) -> None:
        #将路径转化成绝对路径
        ## 数据库存在位置
        self.db_path=os.path.abspath(db_path).replace("\\","/")
        ## 文件路径
        self.file_path=os.path.abspath(file_path).replace("\\","/")
        #是否要在origin中写入
        self.write_origin=write_origin
        #是否检查已有的文件
        self.check_exist=check_exist
        #文件的操作时间
        self.time=fileTime()
        #打开Log文件夹
        Log.open(self.db_path,self.time)
        Log.writeLog(f"add --db {db_path} --files {file_path} --writeOrigin {write_origin} --checkExist {check_exist}")
        #打开数据库
        database=os.path.join(db_path,"files.db")
        self.conn=sqlite3.connect(database)
        self.cur=self.conn.cursor()

        self.run()

        self.conn.commit()
        self.conn.close()

    def run(self):
        #exists是一个字典，key是path值，value是一个file的列表，记录了所有在数据库中的文件
        exists_path={}
        exists_hashkey={}
        #在文件夹存在，且在数据库中有记录的文件，存放的是路径
        exist_set=[]
        #在文件夹中存在，且不在数据库中的文件，存放的是路径
        not_exist_set=[]

        #存在于数据库，但是已经不存在的列表,存放的是路径
        disappear_file={}
        #存在于数据库，但是发生了数据改变的列表，存放的是路径
        hash_change={}


        check_removed={}

        sizes=sizeManage(self.file_path)



        #提取数据库中已经存在的

        to_match=self.file_path+"%"
        files=self.cur.execute("SELECT * FROM now WHERE path LIKE ?",(to_match,)).fetchall()
        for i in files:
            exists_path[i[3]]=i #以路径代表的字典
            exists_hashkey[i[1]]=i #以哈希值代表的字典
        Log.writeLog(f"collect {len(exists_path)} exist files from database")

        #生成要检查的文件，并将要检查的文件分为有记录的的和不存在的
        for root,dir,files in os.walk(self.file_path):
            for file in files:
                #忽略redirect文件
                if file=="redirect.txt":
                    continue
                else:
                    path=os.path.join(root,file).replace("\\","/")
                    if path in exists_path:
                        exist_set.append(path)
                    else:
                        not_exist_set.append(path)
        Log.writeLog(f"collect {len(exist_set)} recorded files and {len(not_exist_set)} not recorded files")

        #截止到这里，生成了三个set
        ## 第一个是一个字典，提取自原始数据库，其中key为文件的目录，value为数据库存储文件的形式
        ## 第二个是名为“exist_set”的list，存放现在存在于文件夹中，同时存在于数据库中的文件路径
        ## 第三个是名为“not_exist_set”的list，存放有现存于文件夹中，但是不存在于数据库中的文件路径

        if self.check_exist:
            for i in exists_path.keys():
                #如果在数据库中存在，但是实际路径区域不存在，记入removed
                if not os.path.exists_path(i):
                    f=exists_path[i]
                    disappear_file[exists_path[i][1]]=exists_path[i]
                    #self.cur.execute("INSERT INTO change (time,hashMd5,conflictNum,path) VALUES (?,?,?,?)",(self.time,exists_path[i][1],exists_path[i][2],"removed"))
                    #self.cur.execute("DELETE FROM now WHERE hashMd5=? AND path=?",(exists_path[i][1],i))
                    #check_removed[f[1]]=f
                #如果存在，就查一下哈希
                else:
                    hash=getAHash(i)
                    sizes.update(i)
                    sizes.showProgress()
                    #如果哈希不一致，就当作老的删掉然后加上新的
                    if hash!=exists_path[i][1]:
                        file=[i,exists_path[i][1],hash]
                        #self.cur.execute("INSERT INTO change (time,hashMd5,conflictNum,path) VALUES (?,?,?,?)",(self.time,exists_path[i][1],exists_path[i][2],"removed"))
                        #self.cur.execute("UPDATE now SET hashMd5=? WHERE hashMd5=? AND path=?",(hash,exists_path[i][1],i))
                        hash_change[file[1]]=file
                        Log.writeLog(f"[hash not match]\t{file[0]} \toldhash:{file[1]}\tnewhash\t{file[2]}")
            self.conn.commit()
            Log.writeLog("finished check recorded file")
        else:
            sizes.update(exist_set)
            sizes.showProgress()


        #到这一步，构建了disappear_file用来记录消失的文件和hash_change用来记录哈希改变的文件


        for path in not_exist_set:
            #先拿哈希值
            hash=getAHash(path)
            sizes.update(path)
            sizes.showProgress()
            
            #如果是消失的文件，说明发生了一次移位

            #如果是哈希改变的文件，说明发生了一次移位-写入

            #如果都不是，说明是新文件

            ## 如果没有冲突，直接写入

            ## 如果有哈希冲突

            ### 如果确实相同，判别，删除

            ### 如果哈希碰撞 上报
            
            # if not hash in exists_hashkey:
            #     self.cur.execute("INSERT INTO now (time,hashMd5,conflictNum,path) VALUES (?,?,?,?)",(self.time,hash,0,path))
            #     if self.write_origin and not hash in check_removed:
            #         self.cur.execute("INSERT INTO origin (time,hashMd5,conflictNum,path) VALUES (?,?,?,?)",(self.time,hash,0,path))
            #     else:
            #         self.cur.execute("INSERT INTO change (time,hashMd5,conflictNum,path) VALUES (?,?,?,?)",(self.time,hash,0,path))
            #     if hash in check_removed:
            #         del check_removed[hash]
            # else:
            #     file=exists_hashkey[hash]
            #     if os.path.exists_path(file[3]) and compareFile(file[3],path):
            #         if self.write_origin:
            #             self.cur.execute("INSERT INTO origin (time,hashMd5,conflictNum,path) VALUES (?,?,?,?)",(self.time,hash,0,path))
            #         self.conn.commit()
            #         removeFile(path)
            #     elif not os.path.exists_path(file[3]):
            #         self.cur.execute("INSERT INTO change (time,hashMd5,conflictNum,path) VALUES (?,?,?,?)",(self.time,hash,file[2],path))
            #         self.cur.execute("UPDATE now SET path=? WHERE hashMd5=? AND path=?",(path,hash,file[3]))
            #     else:
            #         Log.writeLog(f"[hash conflict] hash as {hash} in path {path} and {file[3]}")
            
        for i in check_removed.keys():
            self.cur.execute("INSERT INTO change (time,hashMd5,conflictNum,path) VALUES (?,?,?,?)",(self.time,i,check_removed[i][2],"removed"))
            

    