from FileList import *
from AFile import *
from Hash import *
import os
class Check:
    def __init__(self,path) -> None:
        self.downloadList=FileList("./fileLogs/download/new.txt")
        self.res=open("./fileLogs/samePath.txt",'w',encoding="utf-8")
        self.check(path)
    def check(self,path:str):
        if os.path.isdir(path):
            allSame=True
            truePath=[]
            fl=os.listdir(path)
            for i in fl:
                p=os.path.join(path,i)
                if self.check(p):
                    truePath.append(p)
                else:
                    allSame=False
            if allSame:
                return True
            else:
                for i in truePath:
                    self.res.write(i+"\n")
                return False
        else:
            p=getAHash(path)
            f=self.downloadList.findHash(p)
            if f:
                return True
            else:
                return False
                
if __name__=="__main__":
    path="/mnt/using/anime/unchecked"
    Check(path)