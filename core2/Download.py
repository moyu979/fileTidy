import sys
from FileList import *
from Hash import *
from fileTime import *
from RemoveFile import * 
from Log import *        
def download(path):
    Log.writeLog("Download:\n")
    #计算此次文件哈希值
    hash=GeneHash()
    filelist=hash.run(path)
    motherPath="./fileLogs/download/"

    mpath=os.path.abspath(motherPath)
    
    newPath=os.path.join(mpath,"new.txt")
    timePath=os.path.join(mpath,fileTime()+".txt")
    
    #读入已经存在的
    downloadList=FileList(newPath)

    print("combining")
    sameFile,notExistFile=downloadList.combineNoSame(filelist)
    print("removing")
    removeFiles(sameFile)
    if len(notExistFile)!=0:      
        lossSame=FileList()
        lossSame.fileList=notExistFile
        lossSame.outPut(timePath.replace(".txt","_loss.txt"))
    downloadList.outPut(newPath)
    downloadList.outPut(timePath)
    
        
if __name__ == "__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入下载文件存储路径")
    path=os.path.abspath(path)
    aft=download(path)