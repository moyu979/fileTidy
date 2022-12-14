import os
import sys
from getFileTime import *

class init:
    def __init__(self,path:str):
        self.workPath=os.path.join(path,"fileDirs")
        if not os.path.exists(self.workPath):
            os.mkdir(self.workPath)
            
    def initdownloadFile(self):
        destPath=os.path.join(self.workPath,"downloads")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            print(os.path.relpath(destPath)+" inited")  
        newly=os.path.join(destPath,"new.txt")
        if not os.path.exists(newly):
            with open(newly,"w") as f:
                f.close()
            print(os.path.relpath(newly)+" inited")
            
    def initTidy(self):
        destPath=os.path.join(self.workPath,"tidys")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            print(os.path.relpath(destPath)+" inited")  
        newly=os.path.join(destPath,"new.txt")
        if not os.path.exists(newly):
            with open(newly,"w") as f:
                f.close()
            print(os.path.relpath(newly)+" inited")
    
    def initunzip(self):
        destPath=os.path.join(self.workPath,"unzips")
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
                t=getFileTime()
                f.write(t)
                f.write("\n")
                f.close()
            print(os.path.relpath(destPath)+" inited")
        
            
    
if __name__ =="__main__":
    if len(sys.argv)!=2:
        #print(len(sys.argv),"argvs "+"not match")
        x=init(os.path.abspath("."))
    else:
        x=init(sys.argv[1])
    for i,j in init.__dict__.items():
        if callable(j) and i!="__init__":
            j(x)            