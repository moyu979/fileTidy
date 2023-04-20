from AFile import *
from FileList import FileList
import os
from fileTime import *
from Hash import GeneHash
from Log import *
import sys

def aftermove(finalPath):
    
    Log.writeLog("afterMove "+finalPath)

    finalList=FileList("./fileLogs/final/new.txt")
    tidyList=FileList("./fileLogs/tidy/new.txt")
    
    nowFinalPath=[]
    notExist=[]

    #收集目录下所有文件路径
    for curDir, dirs, files in os.walk(finalPath):
        for file in files:
            if file!="redirect.txt":
                p=os.path.join(curDir, file)
                nowFinalPath.append(os.path.abspath(p))
    #筛出不在记录里的
    for i in nowFinalPath:
        if not finalList.findPath(i):
            notExist.append(i)

    #生成不存在文件的哈希 
    h=GeneHash()
    notExistHash=h.run(notExist)

    middleList=FileList()

    #在tidy找到的和没找到的都归进middle
    i:AFile
    for i in notExistHash:
        #从tidyList取出
        file=tidyList.findHash(i.hashMd5)
        if file:
            tidyList.deleteByHash(i.hashMd5)
            #添加变化路径(输出时会重新生成nowPath)
            file.changePath.append(i.changePath[0])
            #加到FinalList
            middleList.append(file)
        else:
            file=AFile()
            file.hashMd5=i.hashMd5
            file.nowPath=i.nowPath
            file.changePath=i.changePath
            file.noSourceFile=True

            middleList.append(file)
            
            log.writeLog("[afterremove more file]"+i.nowPath)
    #tidy中删除的归到middle
    for i in tidyList:
        if i.removed:
            middleList.append(i)
            tidyList.deleteByHash(i.hashMd5)

    conflict=FileList()
    
            
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
    if len(sys.argv)==1:
        path=input("请输入测试路径")
    else:
        path=sys.argv[1]
    aftermove(path)