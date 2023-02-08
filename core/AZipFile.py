import os
from Hash import *
import log


#输入一个存有压缩文件-解压文件夹关系对的目录，生成压缩文件哈希和解压文件哈希关系
class AZipFile:
    def __init__(self,path):
        self.path=path
        self.zipHash=""
        self.fileList=[]
        self.error=False

        self.get(path)
        
    def get(self,path):
        zipcount=0
        dircount=0
        
        inzipFile=os.listdir(self.path)
        
        #检查数据是否能匹配
        for i in inzipFile:
            p=os.path.join(path,i)
            if p.endswith(".zip") or p.endswith(".rar") or p.endswith(".7z"):
                zipcount=zipcount+1
            if os.path.isdir(p):
                dircount=dircount+1
                
        #数据错误处理
        if not zipcount==1:
            string=""
            string=string+self.path+"[more zip file] has more than one zip file, which is "+str(zipcount)
            log.writeLog(string)
            self.error=True
            return
        
        fileList=[]
        #获取数据
        for i in inzipFile:
            p=os.path.join(path,i)
            if p.endswith(".zip") or p.endswith(".rar") or p.endswith(".7z"):
                hash=getAHash(path)
                self.zipHash=[hash,path]
            else:
                hash=GeneHash()
                hashList=hash.run(p)
                fileList.append(hashList)
        #对比多次解压的内容是否相同    
        for i in range(1,dircount):
            self.compare(fileList[0],fileList[i])
        #提取解压文件的哈希值    
        for i in fileList[0]:
            self.fileList.append([i.hashMd5,i.nowPath])    
    #判别两个文件夹中的文件是否完全一致            
    def compare(self,a:FileList,b:FileList):
        a.sortByHash()
        b.sortByHash()
        for i in range(0,len(a.fileList)):
            if a.fileList[i].hashMd5!=b.fileList[i].hashMd5:
                string="there is an error in \""+self.path+"\" please check"
                log.writeLog("[zip or unzip error]"+string)
                self.error=True
                break

    def hasHash(self,hash):
        if self.zipHash[0]==hash:
            return True
        for i in self.fileList:
            if i[0]==hash:
                return True
        return False     
    
    def __str__(self) -> str:
        string=""
        if self.error:
            string="there is an error in "+self.path+" please check\n"
        else:
            string=string+self.zipHash[0]+"::"+self.zipHash[1]+"\n"
            for i in self.fileList:
                string=string+i[0]+"::"+i[1]+"\n"
        return string
    
    