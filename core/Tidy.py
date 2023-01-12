from FileList import *
from Hash import *
from AFile import *
from FileTime import *
from AZipFile import *
import Log
import copy
class AfterTidy:
    #改，改成以tidyfile为核心的
    def __init__(self,path=None) -> None:
        #temp files
        #list of AZipList
        self.zipList=[]
        self.unzipList=[]
        
        self.tidyList=FileList()
        self.deleteList=FileList()
        self.downloadList=FileList()
        self.final=FileList()
        
        self.downloadList.importFileList("./fileLogs/download/new.txt")
        
        if path:
            self.start(path)
    
    def getTidyList(self,path):
        tidyPath=os.path.join(path,"tidy")
        tidyList=GeneHash().start(tidyPath) #生成整理后文件的文件列表
        sameFile=self.tidyList.combine(tidyList) #获取相同文件表
        #删除文件
        removeFiles(sameFile)
    
    def getUnzipList(self,path):
        unzipPath=os.path.join(path,"unzip")
        unzips=os.listdir(unzipPath)
        for i in unzips:
            dir=os.path.join(unzipPath,i)
            k=AZipFile(dir)
            if not k.error:
                self.unzipList.append(k)
            else:
                Log.writeLog(k.path+" has error")

    def getZipList(self,path):
        zipPath=os.path.join(path,"zip")
        zips=os.listdir(zipPath)
        for i in zips:
            dir=os.path.join(zipPath,i)
            k=AZipFile(dir)
            if not k.error:
                self.zipList.append(k)      
            else:
                Log.writeLog(k.path+" has error") 
    def getDeleteList(self,path):
        deletePath=os.path.join(path,"delete")
        h=GeneHash()     
        self.deleteList=h.start(deletePath)
    def start(self,path):
        #计算整理好的文件的哈希
        self.getTidyList(path)
        self.getUnzipList(path)
        self.getZipList(path)
        self.getDeleteList(path)
        
        i:AFile
        for i in self.tidyList:
            dfile=copy.deepcopy(self.downloadList.findHash(i.hashMd5))
            zfile=[]
            ufile=[]
            j:AZipFile
            for j in self.zipList:
                if j.hasHash(i.hashMd5):
                    zfile.append(j)
            for j in self.unzipList:
                if j.hasHash(i.hashMd5):
                    ufile.append(j)
            #原来就有,否则新建            
            if dfile:
                pass
                #用visited字段做确认来源标记
                dfile.visited=True
                self.downloadList.deleteByHash(dfile.hashMd5)
            else:
                dfile=AFile()
                dfile.hashMd5=i.hashMd5
                
        
            
            for j in zfile:
                if j.zipHash==i.hashMd5:
                    for k in j.fileList:
                        dfile.zipFrom.add(k)
                        dfile.visited=True
            print(len(zfile))            
            for k in zfile:
                print(k)
            for j in ufile:
                #不是压缩文件，自然是解压来的
                if j.zipHash!=i.hashMd5:
                    dfile.unzipFrom.add(j.zipHash)
                    dfile.visited=True
                    
            #tidyList的orig就是现在的位置        
            for s in i.originPath:
                if os.path.exists(s):
                    dfile.changePath.append(s)
                    
            if not dfile.visited:    
                Log.writeLog("[more file]\tfind no source File "+dfile.hashMd5+dfile.changePath[0])
            self.final.addAFile(dfile)
            #查找解压文件夹有没有丢件
            j:AZipFile
            for j in zfile:
                #k:[hash,path]
                for k in j.fileList:
                    if (not self.final.findHash(k[0])) and (not self.deleteList.findHash(k[0])):
                        Log.writeLog("[loss file]\t "+k[0]+" "+k[1]) 
        i:AFile    
        j:AFile
        for i in self.deleteList:
            de=copy.deepcopy(self.downloadList.findHash(i.hashMd5))
            de.removed=True
            self.final.addAFile(de)
                
        
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