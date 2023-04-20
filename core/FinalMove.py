import os
from _FileList import *
from _Hash import *
import log
#有一些问题，多Path移动没写
def finalMove(path):
    
    notInList=[]
    nowFinalPath=[]
    finalList=FileList("./fileLogs/final/new.txt")
    tidyList=FileList("./fileLogs/tidy/new.txt")
    #遍历整个文件夹的路径
    for curDir, dirs, files in os.walk(path):
        for file in files:
            p=os.path.join(curDir, file)
            nowFinalPath.append(os.path.abspath(p))
    #如果路径不存在于列表中
    for i in nowFinalPath:
        if not finalList.findPath(i):
            notInList.append(i)
            
    notInListHash=GeneHash().run(notInList)
    i:AFile 
    for i in notInListHash:
        file=tidyList.findHash(i.hashMd5)
        if file:
            file.changePath.append(i.changePath[0])
            file.autoupdate()
        else:
            log.writeLog("[final move more file] find not loged file "+i)
            file=AFile()
            file=i
        finalList.addAFile(file)
        
if __name__ == "__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入最终存储路径")
    path=os.path.abspath(path)
    finalMove(path)
    