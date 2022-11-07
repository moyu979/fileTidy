from posixpath import join
import os
import sys
from geneHash import * 
from AFile import *
destList=open("./workPath/destList/dest.txt",'w')

class beforeMove:
    def __init__(self):
        self.nowpath=""
        self.moveto=""
        
    def setPath(self,nowPath,moveTo):
        print("请输入现在文件存放位置")
        print("请输入文件转移位置")
        
    def beforeMove(nowPath,movePath):
        if os.path.isdir(nowPath):
            for i in os.listdir(nowPath):
                j=os.path.join(nowPath,i)
                beforeMove(j)
    
        