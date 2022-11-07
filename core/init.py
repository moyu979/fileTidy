from FileList import *
from AFile import *

from posixpath import join
import os
import sys


class init:
    def __init__(self,path:str):
        self.workPath=os.path.join(path,"fileDirs")
        if not os.path.exists(self.workPath):
            os.mkdir(self.workPath)
            
    
    def initDownloads(self):
        destPath=os.path.join(self.workPath,"downloads")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            newly=os.path.join(destPath,"new.txt")
            with open(newly,"w") as f:
                f.close()
    
    def initzip(self):
        destPath=os.path.join(self.workPath,"zip")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            newly=os.path.join(destPath,"new.txt")
            with open(newly,"w") as f:
                f.close()
    
    def initunzip(self):
        destPath=os.path.join(self.workPath,"unzip")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            newly=os.path.join(destPath,"new.txt")
            with open(newly,"w") as f:
                f.close()
    
    def initorganized(self):
        destPath=os.path.join(self.workPath,"organized")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            newly=os.path.join(destPath,"new.txt")
            with open(newly,"w") as f:
                f.close()
            
    def initfinal(self):
        destPath=os.path.join(self.workPath,"final")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            newly=os.path.join(destPath,"new.txt")
            with open(newly,"w") as f:
                f.close()
    
    def inittemp(self):
        destPath=os.path.join(self.workPath,"temp")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            newly=os.path.join(destPath,"new.txt")
            with open(newly,"w") as f:
                f.close()
            

if __name__ =="__main__":
    if len(sys.argv)!=2:
        #print(len(sys.argv),"argvs "+"not match")
        x=init(os.path.abspath("."))
    else:
        x=init(sys.argv[1])
    for i,j in init.__dict__.items():
        if callable(j) and i!="__init__":
            print(i.replace("init","init "))
            j(x)
