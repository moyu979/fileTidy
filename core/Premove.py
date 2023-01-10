from FileList import *
from AFile import *
from RemoveFile import *
from CompareFile import *
#只检查在tidy文件夹里的东西和final归档的是否相同，如果相同，直接搞
def premove():
    finalList=FileList("./fileLogs/final/new.txt")
    tidyList=FileList("./fileLogs/tidy/new.txt")
    i:AFile
    for i in tidyList:
        same=finalList.findHash(i.hashMd5)
        if same:
            #如果相同 并且对比相同，执行合并，否则不管
            if compareFile(same.nowPath,i.nowPath):
                removeFile(i)
                for j in i.originPath:
                    same.originPath.add(i)
                for j in i.zipFrom:
                    same.zipFrom.add(j)
                for j in i.unzipFrom:
                    same.unzipFrom.add(j)
                    
if __name__=="__main__":
    premove()
    
        
        
        