from FileList import *
from generateHash import *
from AFile import *
from log import *
from AZipFile import *
class AfterTidy:
    def __init__(self,path=None) -> None:
        #temp files
        #list of AZipList
        self.zipList=[]
        self.unzipList=[]
        self.tidyList=FileList()
        
        self.downloadList=FileList()
        self.final=FileList()
        
        self.log=Log()
        
        self.downloadList.importFileList("./fileDirs/downloads/new.txt")
        
        if path:
            self.start(path)
            
    def start(self,path):
        #计算整理好的文件的哈希
        self.getTidyList(path)
        self.getUnzipList(path)
        self.getZipList(path)
        #将对应项调到final里
        for i in self.zipList:
            pass
        
                
    def getTidyList(self,path):
        tidyPath=os.path.join(path,"tidy")
        tidyList=GeneHash().start(tidyPath) #生成整理后文件的文件列表
        sameFile=self.tidyList.combine(tidyList) #获取相同文件表
        #删除文件
        for i in sameFile:
            print(i)
        removeFiles(sameFile)
    
    def getUnzipList(self,path):
        unzipPath=os.path.join(path,"unzip")
        unzips=os.listdir(unzipPath)
        for i in unzips:
            dir=os.path.join(unzipPath,i)
            self.unzipList.append(AZipFile(dir))
    
    def getZipList(self,path):
        zipPath=os.path.join(path,"zip")
        zips=os.listdir(zipPath)
        for i in zips:
            dir=os.path.join(zipPath,i)
            self.zipList.append(AZipFile(dir))        
                
if __name__=="__main__":
    afterTidy=AfterTidy()
    print("请输入整理好的文件的存储位置")
    tidyPath=input()
    afterTidy.getTidyList(tidyPath)
    for i in afterTidy.tidyList:
        print(i)
    