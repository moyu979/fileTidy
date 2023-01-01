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
        unfind=FileList()
        
        #处理解压文件夹
        middleList=[]
        i:AZipFile        
        for i in self.unzipList:
            afile=AFile()
            afile.hashMd5=i.zipHash
            
            unzipfile=i.fileList
            for j in unzipfile:
                afile.addUnzip(j)
                
                bfile=AFile()
                bfile.hashMd5=j
                
                middleList.append(bfile)
            
            middleList.append(afile)
        
        #处理压缩文件夹
        i:AZipFile        
        for i in self.unzipList:
            afile=AFile()
            afile.hashMd5=i.zipHash
            
            unzipfile=i.fileList
            for j in unzipfile:
                
                bfile=AFile()
                bfile.hashMd5=j
                bfile.addZip(afile.hashMd5)
                
                middleList.append(bfile)
            
            middleList.append(afile)
            
        #压缩和解压文件预取预设置        
        for i in middleList:
            file=self.downloadList.findHash(i.hashMd5)
            if file:
                #存在的话，提取，写入现在的信息，从download列表删除，加入final
                self.downloadList.deleteByHash(file.hashMd5)
                file.combinewith(i)
                self.final.addAFile(file)
            else:
                #不存在的话直接加入
                self.final.addAFile(i)
                
        #处理tidy文件夹
        i:AFile
        for i in self.tidyList:
            file=self.downloadList.findHash(i.hashMd5)
            if file:
                #如果这个file存在于原始数据中（不是解压而来的或压缩而来的）
                file.addChangePath(i.originPath)
                self.downloadList.deleteByHash(i.hashMd5)
            else:
                #如果这个file是解压而来的或者压缩而来的,或者涉及到了压缩文件，则原本旧不会存在于downloadList，
                #或是已经从download中删除
                file=AFile()
                file.hashMd5=i.hashMd5
                #将生成哈希时的originPath改写为实际的changePath
                file.addChangePath(i.originPath)
            self.final.addAFile(file)
                
                
        
                
                
                
                
        
                
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
    