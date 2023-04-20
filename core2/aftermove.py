from _AFile import *
from _FileList import FileList
import os
from fileTime import *
from Hash import GeneHash
from _Log import *
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
        tidyfile=tidyList.findHash(i.hashMd5)
        finalfile=finalList.findHash(i.hashMd5)
        #如果final里有这个，说明被标记成removed了
        if tidyfile and finalfile:
            tidyList.deleteByHash(i.hashMd5)
            finalfile.removed=False
            finalfile.autoupdate()
            if tidyfile.nowPath!=finalfile.nowPath:
                finalfile.changePath.append(file.nowPath)
            finalfile.originPath.add(file.originPath)
        elif tidyfile:
            tidyList.deleteByHash(i.hashMd5)
            #添加变化路径(输出时会重新生成nowPath)
            tidyfile.changePath.append(i.changePath[0])
            #加到FinalList
            middleList.append(tidyfile)
        else:
            tidyfile=AFile()
            tidyfile.hashMd5=i.hashMd5
            tidyfile.nowPath=i.nowPath
            tidyfile.changePath=i.changePath
            tidyfile.noSourceFile=True

            middleList.append(tidyfile)
            
            Log.writeLog("[afterremove more file]"+i.nowPath)
    #tidy中删除的归到middle
    for i in tidyList:
        if i.removed:
            middleList.append(i)
            tidyList.deleteByHash(i.hashMd5)

    conflict=FileList()
    
            
    file=fileTime()+".txt"
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