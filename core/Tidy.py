from FileList import *
from Hash import *
from AFile import *
from FileTime import *
from AZipFile import *
import Log

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
        self.zipList=h.start(deletePath)
    def start(self,path):
        #计算整理好的文件的哈希
        self.getTidyList(path)
        self.getUnzipList(path)
        self.getZipList(path)
        self.getDeleteList(path)
        i:AFile
        for i in self.tidyList:
            dfile=self.downloadList.findHash(i.hashMd5)
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
            else:
                dfile=AFile()
                dfile.hashMd5=i.hashMd5
                
        
            j:AZipFile
            for j in zfile:
                if j.zipHash==i.hashMd5:
                    for k in j.fileList:
                        dfile.zipFrom.add(k)
            
            for j in ufile:
                #不是压缩得到的，自然是解压来的
                if j.zipHash!=i.hashMd5:
                    dfile.unzipFrom.add(j.zipHash)
                    
            for s in i.originPath:
                if os.path.exists(s):
                    dfile.changePath.append(s)
                
            self.final.addAFile(dfile)
        i:AFile    
        j:AFile
        for i in self.deleteList:
            for j in self.downloadList:
                j.removed=True
                
        
                
        
                    
        # #将对应项调到final里
        # middleList=[]
        # #处理解压文件夹
        # i:AZipFile        
        # for i in self.unzipList:
            
        #     afile=AFile()
        #     afile.hashMd5=i.zipHash
        #     afile.removed=True
        
        #     unzipfile=i.fileList
        #     for j in unzipfile:
                
        #         bfile=AFile()
        #         bfile.hashMd5=j
        #         bfile.addUnzip(afile.hashMd5)
                
        #         middleList.append(bfile)
            
        #     middleList.append(afile)
        
        # #处理压缩文件夹
        # i:AZipFile        
        # for i in self.zipList:
        #     afile=AFile()
        #     afile.hashMd5=i.zipHash
            
        #     unzipfile=i.fileList
        #     for j in unzipfile:
                
        #         bfile=AFile()
        #         bfile.hashMd5=j
        #         bfile.removed=True
        #         afile.addZip(bfile.hashMd5)
        #         middleList.append(bfile)
            
        #     middleList.append(afile)
            
        # i:AFile
            
        # #压缩和解压文件预取预设置        
        # for i in middleList:
        #     file=self.downloadList.findHash(i.hashMd5)
        #     if file:
        #         #存在的话，提取，写入现在的信息，从download列表删除，加入final
        #         self.downloadList.deleteByHash(file.hashMd5)
        #         file.combinewith(i)
        #         self.final.addAFile(file)
        #     else:
        #         print(i.hashMd5)
        #         #不存在的话直接加入
        #         self.final.addAFile(i)
                
        # #处理tidy文件夹
        # i:AFile
        # for i in self.tidyList:
        #     downLoadFile=self.downloadList.findHash(i.hashMd5)
        #     finalFile=self.final.findHash(i.hashMd5)
        #     if downLoadFile:
        #         #如果这个file存在于原始数据中（不是解压而来的或压缩而来的）
        #         downLoadFile.addChangePath(i.changePath[0])
        #         self.downloadList.deleteByHash(i.hashMd5)
        #         self.final.addAFile(downLoadFile)
        #     elif finalFile:
        #         #如果i已经被放入finalFile(压缩过的什么的)
        #         finalFile.addChangePath(i.changePath[0])
        #     else:
        #         #新文件
        #         l="not find "+i.hashMd5+" "+i.nowPath
        #         Log.writeLog(l)


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