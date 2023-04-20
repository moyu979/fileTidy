from _FileList import *
from _AFile import *
from _Hash import *
import os
#查看某个文件夹下的文件是否在tidy中
class Check:
    def __init__(self,path) -> None:
        self.downloadList=FileList("./fileLogs/tidy/new.txt")
        self.res=open("./fileLogs/inTidy.txt",'w',encoding="utf-8")
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
                
if __name__ == "__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入要检查的文件或文件夹")
    path=os.path.abspath(path)
    Check(path)
