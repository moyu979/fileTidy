from AFile import *
from FileList import FileList
import os
from FileTime import *
from Hash import GeneHash
import log

def aftermove(finalPath):
    log.writeLog(FileTime()+"")
    finalList=FileList("./fileLogs/final/new.txt")
    tidyList=FileList("./fileLogs/tidy/new.txt")
    nowFinalPath=[]
    notExist=[]
    for curDir, dirs, files in os.walk(path):
        for file in files:
            if file!="redirect.txt":
                p=os.path.join(curDir, file)
                nowFinalPath.append(os.path.abspath(p))
    #筛出不在记录里的
    for i in nowFinalPath:
        if finalList.findPath(i):
            pass
        else:
            notExist.append(i)
     
    notExistHash=GeneHash().startFileList(notExist)
    i:AFile
    for i in notExistHash:
        #从tidyList取出
        file=tidyList.findHash(i.hashMd5)
        if file:
            tidyList.deleteByHash(i.hashMd5)
            #添加变化路径(输出时会重新生成nowPath)
            file.changePath.append(i.changePath[0])
            #加到FinalList
            finalList.addAFile(file)
        else:
            log.writeLog("[afterremove more file]"+i.nowPath)
    for i in tidyList:
        if i.removed:
            finalList.addAFile(i)
            tidyList.deleteByHash(i.hashMd5)
    file=FileTime()+".txt"
    final1="./fileLogs/final/new.txt"
    final2="./fileLogs/final/"+file
    tidy1="./fileLogs/tidy/new.txt"
    tidy2="./fileLogs/tidy/"+file
    
    finalList.outPut(final1)
    finalList.outPut(final2)
    tidyList.outPut(tidy1)
    tidyList.outPut(tidy2)
    
if __name__=="__main__":
    path="/mnt/anime8T1/animes"
    aftermove(path)