from FileList import *
from Hash import *
from AFile import *
from FileTime import *
from AZipFile import *
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
        
        self.downloadList.importFileList()
        
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
            self.deleteList=h.run(deletePath)
        else:
            log.writeLog("no delete file")
            
    def start(self,path):
        log.writeLog("Tidy:"+FileTime())
        #计算整理好的文件的哈希
        self.getTidyList(path)
        self.getUnzipList(path)
        self.getZipList(path)
        self.getDeleteList(path)
        
        i:AFile
        for i in self.tidyFile:
            zfile=[]
            ufile=[]
            j:AZipFile
            for j in self.zipList:
                if j.hasHash(i.hashMd5):
                    zfile.append(j)
            for j in self.unzipList:
                if j.hasHash(i.hashMd5):
                    ufile.append(j)
            dfile=copy.deepcopy(self.downloadList.findHash(i.hashMd5))
            #原来就有,否则新建            
            if dfile:
                #用visited字段做确认来源标记
                dfile.visited=True
                self.downloadList.deleteByHash(dfile.hashMd5)
            else:
                dfile=AFile()
                dfile.hashMd5=i.hashMd5
                
            #压缩而来和解压而来的标记(zipfrom unzipfrom)    
            for j in zfile:
                if j.zipHash[0]==dfile.hashMd5:
                    for k in j.fileList:
                        dfile.zipFrom.add(k)
                        dfile.visited=True
            for j in ufile:
                #不是压缩文件，自然是解压来的
                if j.zipHash[0]!=i.hashMd5:
                    dfile.unzipFrom.add(j.zipHash)
                    dfile.visited=True
                    
            #tidyList的orig就是现在的位置        
            for s in i.originPath:
                if os.path.exists(s):
                    dfile.changePath.append(s)
                    
            if not dfile.visited:    
                dfile.noSourceFile=True
                log.writeLog("[more file]\tfind no source File "+dfile.hashMd5+dfile.changePath[0])
                
            self.tidyList.addAFile(dfile)
            dfile.autoupdate()
        #————————————至此tidy文件夹内有的文件全部应当找到了对应项————————————————
        #delete文件归入
        for i in self.deleteList:
            file=self.tidyList.findHash(i.hashMd5)
            file2=self.downloadList.findHash(i.hashMd5)
            if file:
                log.writeLog("[find removed] tidy file:"+file.nowPath+" removed in "+i.nowPath)
            if file2:
                self.downloadList.deleteByHash(file2.hashMd5)
                file2.removed=True
                self.tidyList.addAFile(file2)
            if not file and not file2:
                file3=AFile()
                file3.hashMd5=i.hashMd5
                file3.removed=True
                self.tidyList.addAFile(file3)  
        #unzip文件扫尾
        i:AZipFile
        for i in self.unzipList:
            zipFile=i.zipHash
            for j in i.fileList:
                file=self.tidyList.findHash(j[0])
                if file:
                    file.unzipFrom.add(zipFile)
                else:
                    log.writeLog("[unzipfile lost ]"+j[0]+"::"+j[1])
                    
        #zip文件扫尾        
        i:AZipFile
        for i in self.zipList:
            zipFile=i.zipHash
            file=self.tidyList.findHash(zipFile[0])
            if file:
                for j in i.fileList:
                    file.zipFrom.add(j)
            else:
                log.writeLog("[zipfile lost ]"+zipFile[0]+"::"+zipFile[1])
   
        dataname=FileTime()
    
        dir="./fileLogs"
        down1=dir+"/download/"+dataname+".txt"
        down2=dir+"/download/new.txt"
        tidy1=dir+"/tidy/"+dataname+".txt"
        tidy2=dir+"/tidy/new.txt"
        
        self.downloadList.outPut(down1)
        self.downloadList.outPut(down2)
        self.final.outPut(tidy1)
        self.final.outPut(tidy2)
        
if __name__=="__main__":
    
    print("请输入整理好的文件的存储位置")
    tidyPath=input()
    p=os.path.abspath(tidyPath)
    afterTidy=AfterTidy(p)