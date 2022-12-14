from FileList import *
from generateHash import *
from AFile import *

class AfterTidy:
    def __init__(self) -> None:
        #[zipfile,[all files in zip]]
        self.zipList=[]
        self.unzipList=[]
        self.tidyList=FileList()
        self.downloadList=FileList()
        
        self.downloadList.importFileList("./fileDirs/downloads/new.txt")
        
    
    def getTidyList(self,path):
        tidyList=GeneHash().start(path)
        sameFile=tidyList.combine(tidyList)
        for i in sameFile:
            print(i)
        removeFiles(sameFile)
    
    def getUnzipList(self,path):
        pass
    
    def getZipList(self,path):
        zips=os.listdir(path)
        for i in zips:
            self.zipList.append(self.getAZip(i))
        pass
        
    
if __name__=="__main__":
    afterTidy=AfterTidy()
    print("请输入整理好的文件的存储位置")
    tidyPath=input()
    afterTidy.getTidyList(tidyPath)
    for i in afterTidy.tidyList:
        print(i)
    