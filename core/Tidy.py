from _FileList import *
from _Hash import *
from _AFile import *
from FileTime import *
from _AZipFile import *
import log
import copy
import os
class AfterTidy:
    def __init__(self,path=None) -> None:
        #temp files
        #list of AZipList
        self.zipList=[]
        self.unzipList=[]
        
        self.tidyFile=FileList()
        self.deleteList=FileList()
        self.downloadList=FileList("./fileLogs/download/new.txt")
        self.tidyList=FileList("./fileLogs/tidy/new.txt")
        
        if path:
            self.start(path)
    
    def getTidyList(self,path):
        print("get Tidy")
        tidyPath=os.path.join(path,"tidy")
        if os.path.exists(tidyPath):
            tidyFile=GeneHash().run(tidyPath) #生成整理后文件的文件列表
            sameFile=self.tidyFile.combine(tidyFile) #获取相同文件表
            #删除文件
            removeFiles(sameFile)
        else:
            log.writeLog("no tidy file")
    
    def getUnzipList(self,path):
        print("get unzip")
        unzipPath=os.path.join(path,"unzip")
        if os.path.exists(unzipPath):
            unzips=os.listdir(unzipPath)
            for i in unzips:
                dir=os.path.join(unzipPath,i)
                k=AZipFile(dir)
                if not k.error:
                    self.unzipList.append(k)
                else:
                    log.writeLog("[unzip error]"+k.path+" has error")
        else:
            log.writeLog("no unzip file")

    def getZipList(self,path):
        print("get zip")
        zipPath=os.path.join(path,"zip")
        if os.path.exists(zipPath):
            zips=os.listdir(zipPath)
            for i in zips:
                dir=os.path.join(zipPath,i)
                k=AZipFile(dir)
                if not k.error:
                    self.zipList.append(k)
                else:
                    log.writeLog("[zip error]"+k.path+" has error")
        else:
            log.writeLog("no zip file")
            
    def getDeleteList(self,path):
        print("get delete")
        deletePath=os.path.join(path,"delete")
        if os.path.exists(deletePath):
            h=GeneHash()     
            delete=h.run(deletePath)
            same=self.deleteList.combine(delete)
            removeFiles(same)
        else:
            log.writeLog("no delete file")
            
    def start(self,path):
        log.writeLog("Tidy:"+FileTime())
        #计算整理好的文件的哈希
        self.getTidyList(path)
        self.getUnzipList(path)
        self.getZipList(path)
        self.getDeleteList(path)
        
        zipFileInUnzip=[]
        unzipFileInZip=[]
        #所有生成文件写入download
        i:AZipFile
        for i in self.unzipList:
            zipFileInUnzip.append(i.zipHash)
            for j in i.fileList:
                file=AFile()
                file.hashMd5=j[0]
                file.nowPath=j[1]
                file.unzipFrom.add(i.zipHash)
                file.visited=True
                self.downloadList.addAFile(file)
                
        for i in self.zipList:
            file=AFile()
            file.hashMd5=i.zipHash[0]
            file.nowPath=i.zipHash[1]
            file.visited=True
            self.downloadList.addAFile(file)
            for j in i.fileList:
                file.zipFrom.add(j)
                unzipFileInZip.append(j)
                
        #此时download已经包含了一切生成的文件，再从里面砍掉解压的，压缩的和删除的
        for i in zipFileInUnzip:
            file=self.downloadList.findHash(i[0])
            if file:
                file.removed=True
            else:
                file=AFile()
                file.hashMd5=i[0]
                file.originPath.add(i[1])
                file.noSourceFile=True
                file.removed=True
                self.downloadList.addAFile(file)
                log.writeLog("[more file in tidy]"+i[0]+"::"+i[1])
                
        for i in unzipFileInZip:
            file=self.downloadList.findHash(i[0])
            if file:
                file.removed=True
            else:
                file=AFile()
                file.hashMd5=i[0]
                file.originPath.add(i[1])
                file.noSourceFile=True
                file.removed=True
                self.downloadList.addAFile(file)
                log.writeLog("[more file in tidy]"+i[0]+"::"+i[1])
        
        i:AFile
        for i in self.deleteList:
            file=self.downloadList.findHash(i.hashMd5)
            if file:
                file.removed=True
            else:
                log.writeLog("[delete no file in tidy]"+i.hashMd5+i.nowPath)
                
        #一切存在的和删除的都移入新的文件
        for i in self.tidyFile:
            file=self.downloadList.findHash(i.hashMd5)
            if file:
                for j in i.originPath:
                    if os.path.exists(j):
                        file.changePath.append(j)
                self.tidyList.addAFile(file)
                self.downloadList.deleteByHash(file.hashMd5)
            else:
                log.writeLog("[more file in tidy]"+i.__str__())    
                
        for i in self.downloadList:
            if i.removed or i.noSourceFile:
                self.tidyList.addAFile(i)
                self.downloadList.deleteByHash(i.hashMd5)
        
        for i in self.downloadList:
            if i.visited:
                self.tidyList.addAFile(i)
                i.lossFile=True
                self.downloadList.deleteByHash(i.hashMd5)
                
        # download=FileList("./fileLogs/download/new.txt")
        # for i in self.tidyList:
        #     download.deleteByHash(i.hashMd5)
        for i in self.downloadList:
            if i.visited:
                i.lossFile=True        
        dataname=FileTime()
    
        dir="./fileLogs"
        down1=dir+"/download/"+dataname+".txt"
        down2=dir+"/download/new.txt"
        tidy1=dir+"/tidy/"+dataname+".txt"
        tidy2=dir+"/tidy/new.txt"
        
        self.downloadList.outPut(down1)
        self.downloadList.outPut(down2)
        self.tidyList.outPut(tidy1)
        self.tidyList.outPut(tidy2)
    
    
if __name__ == "__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入整理好的文件存储路径")
    path=os.path.abspath(path)
    AfterTidy(path)