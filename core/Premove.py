from FileList import *
from AFile import *
from RemoveFile import *
from compareFile import *
from FileTime import *
import log
#只检查在tidy文件夹里的东西和final归档的是否相同，如果相同，直接搞
def premove():
    finalList=FileList("./fileLogs/final/new.txt")
    tidyList=FileList("./fileLogs/tidy/new.txt")
    i:AFile
    for i in tidyList:
        same=finalList.findHash(i.hashMd5)
        if same:
            log.writeTemp(same.hashMd5+"\n"+same.nowPath+"\n"+i.nowPath,"tidyFinalSame.txt")
                
                    
if __name__=="__main__":
    premove()
    
        
        
        