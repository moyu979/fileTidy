import os
import sys
from FileTime import *
#初始化用于记录文件的目录，命名为fileLogs，仅需要在初始化时调用
#主目录下有记录下载文件的“download”，记录整理中文件的“tidy”和记录文件的final，
class init:
    def __init__(self,path:str="."):
        path=os.path.abspath(path)
        #记录主目录
        self.workPath=os.path.join(path,"fileLogs")
        if not os.path.exists(self.workPath):
            os.mkdir(self.workPath)
        self.callInit()
            
    def initdownloadFile(self):
        destPath=os.path.join(self.workPath,"download")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            print(os.path.relpath(destPath)+" inited")  
        newly=os.path.join(destPath,"new.txt")
        if not os.path.exists(newly):
            with open(newly,"w") as f:
                f.close()
            print(os.path.relpath(newly)+" inited")
            
    def initTidy(self):
        destPath=os.path.join(self.workPath,"tidy")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            print(os.path.relpath(destPath)+" inited")  
        newly=os.path.join(destPath,"new.txt")
        if not os.path.exists(newly):
            with open(newly,"w") as f:
                f.close()
            print(os.path.relpath(newly)+" inited")
    
    def initfinal(self):
        destPath=os.path.join(self.workPath,"final")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            print(os.path.relpath(destPath)+" inited")  
        newly=os.path.join(destPath,"new.txt")
        if not os.path.exists(newly):
            with open(newly,"w") as f:
                f.close()
            print(os.path.relpath(newly)+" inited")
            
    def initlog(self):
        destPath=os.path.join(self.workPath,"logs.txt")
        if not os.path.exists("log.txt"):
            with open(destPath,"w") as f:
                t=FileTime()
                f.write(t)
                f.write("\n")
            print(os.path.relpath(destPath)+" inited")
    
    def callInit(self):
        for i,j in init.__dict__.items():
            if callable(j) and i!="__init__" and i!="callInit":
                j(self)    
            
    
if __name__ =="__main__":
    if len(sys.argv)!=2:
        x=init(os.path.abspath("."))
    else:
        x=init(sys.argv[1])
    x.callInit()