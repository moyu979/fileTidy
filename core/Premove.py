from _FileList import *
from _AFile import *
from core2.RemoveFile import *
from core2.compareFile import *
from FileTime import *
import log
#只检查在tidy文件夹里的东西和final归档的是否相同，如果相同，直接搞
def premove():
    finalList=FileList("./fileLogs/final/new.txt")
    tidyList=FileList("./fileLogs/tidy/new.txt")
    filename="Same"+FileTime()+".txt"
    with open ("./fileLogs/premove/"+filename,"w") as p:
        p.write("")
    i:AFile
    for i in tidyList:
        same=finalList.findHash(i.hashMd5)
        if same:
            print("-------------")
            log.writeTemp(same.hashMd5+"\n"+same.nowPath+"\n"+i.nowPath+"\n","premove/"+filename)
    return filename            
                    
if __name__=="__main__":
    premove()
    
        
        
        