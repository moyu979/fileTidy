from AFile import *
from FileList import *
from FileTime import FileTime
from Hash import *
import shutil

import os
# 当不小心在整理好的文件夹内放入了未登记入download记录的文件时使用，会将记录的文件移出
class CheckIn:
    def __init__(self,checkPath,outPath) -> None:
        self.checkPath=checkPath
        self.outPath=outPath
        self.fileList=FileList("./fileLogs/download/new.txt")
        self.down=FileList()
        self.outDir="./ex"
        self.trueList=[]
    def run(self):
        self.check(self.checkPath)
        self.update()
    def check(self,path):
        nowList=GeneHash().run(path)
        self.down.combine(nowList)
        self.down.outPut("./down.txt")
        i:AFile
        for i in self.down:
            k=self.fileList.findHash(i.hashMd5)
            if k:
                self.down.deleteByHash(i.hashMd5)
        self.down.outPut("./notex.txt")
        #如果是目录的话，递归查找
    #     if os.path.isdir(path):
    #         lpath=os.listdir(path)
    #         allTrue=True
    #         trueList=[]
    #         #记录其子目录的存在情况
    #         for i in lpath:
    #             abs=os.path.join(path,i)
    #             if self.check(abs):
    #                 trueList.append(abs)
    #             else:
    #                 allTrue=False
    #         #子目录全存在，直接将控制全交给上级
    #         if allTrue:
    #             return True
    #         #子目录有不存在的，将所有存在的移动到新的位置，并向上汇报错误
    #         else:
    #             i:str
    #             for i in trueList:
    #                 dest=i.replace(self.checkPath,self.outPath)
    #                 shutil.move(i,dest)
    #                 return False
    #     else:
    #         h=getAHash(path)
    #         a=self.fileList.findHash(h)
    #         if a:
    #             s=h+"::"+path
    #             log.writeTemp(s)
    #             self.trueList.append(s)
    #             return True
    #         else:
    #             return False
    # def update(self):
    #     i:str
    #     for i in self.trueList:
    #         f=i.split("::")
    #         np=f[1].replace(self.checkPath,self.outPath)
    #         if os.path.exists(np):
    #             a=self.fileList.findHash(f[1])
    #             if a:
    #                 a.changePath.append(np)
    #             else:
    #                 log.writeLog("[remp1 not fount in update]"+f[1]+"::"+path)
    #         else:
    #             pass
    #     path1="./fileLogs/download/new.txt"
    #     path2="./fileLogs/download/"+FileTime()
    #     self.fileList.outPut(path1)
    #     self.fileList.outPut(path2)
    
                
if __name__=="__main__":
    p="/mnt/using/anime/dmhyrss/f1"
    q="/mnt/using/anime/dmhyrss/f2"
    # p="C:\\Users\\30278\\Documents\\code\\filetidyup\\1"
    # q="C:\\Users\\30278\\Documents\\code\\filetidyup\\2"
    c=CheckIn(p,q)
    c.run()