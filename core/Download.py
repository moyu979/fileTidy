import sys
from FileList import *
from Hash import *
from FileTime import *

class afterDownload:
    def __init__(self,path=None):
        self.filelist=FileList()
        if path:
            self.doAfterDownload(path)
            
    def doAfterDownload(self,path):
        #计算此次文件哈希值
        hash=GeneHash()
        self.filelist=hash.start(path)
        
        motherPath="./fileLogs/download/"
        mpath=os.path.abspath(motherPath)
        newPath=os.path.join(mpath,"new.txt")
        timePath=os.path.join(mpath,FileTime()+".txt")
        #读入已经存在的
        downloadList=FileList(newPath)
        
        sameFile=downloadList.combine(self.filelist)
        
        removeFiles(sameFile)
            
        downloadList.sortBypath()
        downloadList.outPut(newPath)
        downloadList.outPut(timePath)
        
if __name__ == "__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入下载文件存储路径")
    path=os.path.abspath(path)
    aft=afterDownload(path)