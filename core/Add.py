import sqlite3
import os
import sys

from _Hash import *
from _fileTime import *
from _Log import *
from _compareFile import *
from _removeFile import *
from _sizeManage import *

class Add:
    def __init__(self,db_path,file_path,write_origin,check_exist,delete) -> None:
        #将路径转化成绝对路径
        ## 数据库存在位置
        self.db_path=os.path.abspath(db_path).replace("\\","/")
        ## 文件路径
        self.file_path=os.path.abspath(file_path).replace("\\","/")
        #是否要在origin中写入
        self.write_origin=write_origin
        #是否检查已有的文件
        self.check_exist=check_exist
        #是否删除重复文件
        self.delete=delete
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
        data_base_existed_path={}
        data_bash_existed_hashkey={}

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



        #提取数据库中已经存在的路径
        to_match=self.file_path+"%"
        files=self.cur.execute("SELECT * FROM now WHERE path LIKE ?",(to_match,)).fetchall()

        for i in files:
            data_base_existed_path[i[2]]=i #以路径代表的字典
            data_bash_existed_hashkey[i[1]]=i #以哈希值代表的字典
        Log.writeLog(f"collect {len(data_base_existed_path)} exist files from database")

        #生成要检查的文件，并将要检查的文件分为有记录的的和不存在的
        for root,dir,files in os.walk(self.file_path):
            for file in files:
                #忽略redirect文件
                if file=="redirect.txt":
                    continue
                else:
                    path=os.path.join(root,file).replace("\\","/")
                    if path in data_base_existed_path:
                        exist_set.append(path)
                    else:
                        not_exist_set.append(path)

        Log.writeLog(f"collect {len(exist_set)} recorded files and {len(not_exist_set)} not recorded files")

        #截止到这里，生成了三个set
        ## 第一个是一个字典，提取自原始数据库，其中key为文件的目录，value为数据库存储文件的形式
        ## 第二个是名为“exist_set”的list，存放现在存在于文件夹中，同时存在于数据库中的文件路径
        ## 第三个是名为“not_exist_set”的list，存放有现存于文件夹中，但是不存在于数据库中的文件路径

        if self.check_exist:
            for i in data_base_existed_path.keys():
                #如果在数据库中存在，但是实际路径区域不存在，记入removed
                if not os.path.exists_path(i):
                    self.cur.execute("UPDATE now SET time=?,path=? WHERE path=?",(self.time,"removed",i))
                #如果存在，就查一下哈希
                else:
                    #这个区域的东西应该和existset一致
                    sizes.update(path)
                    sizes.showProgress()
                    now_hash=getAHash(i)
                    old_hash=data_base_existed_path[i][1]
                    #如果哈希不一致，就当作老的删掉然后加上新的
                    if now_hash!=old_hash:
                        Log.writeLog(f"[hash not match]\t{file[0]} \toldhash:{file[1]}\tnewhash\t{file[2]}")
                        self.cur.execute("UPDATE now SET time=?,path=? WHERE hashMd5=?",(self.time,"removed",old_hash))
                        not_exist_set.append(i)
            self.conn.commit()
            Log.writeLog("finished check recorded file")
            Log.writeLog(f"not recorded files raise to {len(not_exist_set)}")
        else:
            Log.writeLog("not check existed file")
            sizes.update(exist_set)
            sizes.showProgress()


        #到这一步，构建了disappear_file用来记录消失的文件和hash_change用来记录哈希改变的文件

        no_confilct=0
        same=0
        conflict=0
        for path in not_exist_set:
            #先拿哈希值
            hash=getAHash(path)
            sizes.update(path)
            sizes.showProgress()

            existed_file=self.cur.execute("SELECT * FROM now WHERE hashMd5=?",(hash,)).fetchall()
            #保持每次写入origin之后，都会写入now，那么可以得知，如果一个东西不在now中存在，那么一定不在origin中

            if self.write_origin:
                self.cur.execute("INSERT INTO origin (time,hashMd5,path,conflictNum) VALUES (?,?,?,?)",(self.time,hash,path,0))
           
            ## 如果没有冲突，直接写入
            if len(existed_file)==0:
                self.cur.execute("INSERT INTO now (time,hashMd5,path,conflictNum) VALUES (?,?,?,?)",(self.time,hash,path,0))
                
            #下面是now中记录了哈希的情况
            else:
                #如果都删掉了
                if len(existed_file)==1 and existed_file[0][2]=="removed":
                    self.cur.execute("UPDATE now SET time=?,path=? where hashMd5=?",(self.time,path,hash))

                #如果没删完
                else:
                    flag=False
                    #有相同的
                    for i in existed_file:
                        if os.path.exists(i[2]) and compare(i[2],path):
                            removeFile(path)
                            flag=True
                    if flag:
                        continue
                    for i in existed_file:
                        if i[2] in data_base_existed_path and not os.path.exists(i[2]):
                            self.cur.execute("UPDATE now SET time=?,path=? where hashMd5=?",(self.time,path,hash))
                            flag=True
                    if flag:
                        continue      
                    #有暂时不存在的
                    for i in existed_file:
                        if not os.path.exists(i[2]):
                            Log.writeLog(f"[file not exist]\tneed to compare {path} and {i[2]}")
                            flag=True
                    if flag:
                        break
                    #都不是，只能是冲突了
                    for i in existed_file:
                        Log.writeLog(f"[hash conflict]\t{path} and {i[2]}")

    

    