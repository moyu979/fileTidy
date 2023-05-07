import sys
import os
from _AFile import *
from _FileList import *
from _Hash import *
from _Log import *
def update(path,dataList):
    alladd=False
    if dataList=="download":
        fileList=FileList("./fileLogs/download/new.txt")
        alladd=False
    elif dataList=="finish":
        fileList=FileList("./fileLogs/tidy/new.txt")
        alladd=True
    
    notLogedPath=[]
    for curDir, dirs, files in os.walk(path):
        for file in files:
            p=os.path.join(curDir, file)
            if file!="redirect.txt" and not fileList.findPath(p):
                notLogedPath.append(p)

        
    notLogedHash=GeneHash().run(notLogedPath)

    notLogedFile:AFile
    for notLogedFile in notLogedHash:
        inLog:AFile=fileList.findHash(notLogedFile.hashMd5)
        if not inLog:
            notLogedFile.noSourceFile=alladd
            fileList.append(notLogedFile)
        else:
            #删除文件复活
            if inLog.removed:
                inLog.removed=False
                inLog.changePath.append(notLogedFile.nowPath)
                Log.writeLog("[awake removed File]\t"+notLogedFile.nowPath.replace("\\","/")+"\t"+notLogedFile.hashMd5+"\n")
            #移动了
            elif not os.path.exists(inLog.nowPath):
                inLog.removed=False
                inLog.changePath.append(notLogedFile.nowPath)
            #存在删除
            else:
                fileList.appendNoSame(notLogedFile)
                print("qqq")
                removeFile(notLogedFile)


    fileList.writeBack()
            

if __name__=="__main__":
    if len(sys.argv)==3:
        path=sys.argv[1]
        dataList=sys.argv[2]
    else:
        path=input("请输入文件存储路径")
        dataList=input("请输入相关联的文件列表")
    Log.writeLog("update "+dataList+" with "+path)
    path=os.path.abspath(path)
    aft=update(path,dataList)