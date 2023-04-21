import sys
from _FileList import *
from _Hash import *
from fileTime import *
from RemoveFile import * 
from _Log import *        
def download(path):
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
    Log.writeLog("Download: "+path)
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入下载文件存储路径")
    path=os.path.abspath(path)
    aft=download(path)