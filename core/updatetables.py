
from turtle import update
from FileList import *
import os
import sys
import hashlib

def updateFileList(oldPath:str,newPath):
    if newPath==None:
        n=oldPath.split(".",maxsplit=1)[0]+"new."+oldPath.split(".",maxsplit=1)[1]
    fileList=FileList()
    fileList.importFileList(oldPath)
    fileList.sort()
    fileList.outPut(newPath)

updateFileList("./work3/bluelogn.txt","./work3/bluelogn2.txt")
updateFileList("./work3/bluen.txt","./work3/bluen2.txt")
     
