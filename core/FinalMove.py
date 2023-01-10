import os
from FileList import *
from Hash import *
import Log
#有一些问题，多Path移动没写
def finalMove(path):
    notInList=[]
    nowFinalPath=[]
    finalList=FileList("./fileLogs/")
    for curDir, dirs, files in os.walk(path):
        for file in files:
            p=os.path.join(curDir, file)
            nowFinalPath.append(os.path.abspath(p))
    
    for i in nowFinalPath:
        if not finalList.findPath(i):
            notInList.append(i)
            
    notInListHash=GeneHash().startFileList(notInList)
    i:AFile
    
    for i in notInListHash:
        file=finalList.findHash(i.hashMd5)
        if file:
            file.changePath.append(i.changePath[0])
            file.autoupdate()
        else:
            Log.writeLog("[error] find not loged file "+i)
        
    
    for i in finalList:
        if not os.path.exists(i):
            Log.writeLog("[error] find lost file "+i.hashMd5)
        
if __name__=="__main__":
    path=input("请输入final的文件夹")
    finalMove(path)
    