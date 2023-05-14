from _AFile import *
from _FileList import *
from fileTime import *
def moveCheck():
    downloadList=FileList("./fileLogs/download/new.txt")
    finalList=FileList("./fileLogs/final/new.txt")

    conflictList=FileList()
    i:AFile
    for i in downloadList:
        if finalList.findHash(i.hashMd5):
            conflictList.append(i)

    conflictList.outPut("./fileLogs/logs/"+fileTime+"_conflict.txt")

if __name__=="__main__":
    moveCheck()
