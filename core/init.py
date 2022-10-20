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
    
    def initzip(self):
        destPath=os.path.join(self.workPath,"zip")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
    
    def initunzip(self):
        destPath=os.path.join(self.workPath,"unzip")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
    
    def initorganized(self):
        destPath=os.path.join(self.workPath,"organized")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            
    def initfinal(self):
        destPath=os.path.join(self.workPath,"final")
        if not os.path.exists(destPath):
            os.mkdir(destPath)
            

if __name__ =="__main__":
    if len(sys.argv)!=2:
        print(len(sys.argv),"argvs "+"not match")
        x=init(os.path.abspath("."))
    else:
        x=init(sys.argv[1])
    for i,j in init.__dict__.items():
        if callable(j) and i!="__init__":
            print(i)
            j(x)
