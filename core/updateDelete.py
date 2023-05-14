import sys
from _FileList import *
from _Hash import *
from fileTime import *
from RemoveFile import * 
from _Log import *   

def delete(path,dataList):
    if dataList=="download":
        fileList=FileList("./fileLogs/download/new.txt")
    elif dataList=="finish":
        fileList=FileList("./fileLogs/tidy/new.txt")
    else:
        fileList=None

    todelete=GeneHash().run(path)
    i:AFile
    for i in todelete:
        inList:AFile=fileList.findHash(i.hashMd5)
        if not inList:
            Log.writeLog("[no File to delete]\t"+i.nowPath+" with  hash "+i.hashMd5)
        elif os.path.exists(inList.nowPath):
            Log.writeLog("[still has file]\thash:"+inList.nowPath+"\t"+i.nowPath)
        else:
            inList.removed=True
    fileList.writeBack()

if __name__=="__main__":
    if len(sys.argv)==3:
        path=sys.argv[1]
        dataList=sys.argv[2]
    else:
        path=input("请输入要删除文件的存储路径")
        dataList=input("删除自哪个文件夹")

    Log.writeLog("Delete "+path+" from "+dataList)

    path=os.path.abspath(path)
    
    fileList=None
    if dataList=="download":
        fileList=FileList("fileLogs/download/new.txt")
    elif dataList=="tidy":
        fileList=FileList("fileLogs/tidy/new.txt")
    elif dataList=="final":
        fileList=FileList("fileLogs/final/new.txt")   
    else:
        Log.writeLog("[para error]\tnot found fileList named "+path)
    if fileList!=None:
        delete(fileList,path)