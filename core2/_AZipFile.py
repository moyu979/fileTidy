import os
from _Hash import *
from _Log import *


#输入一个存有压缩文件-解压文件夹关系对的目录，生成压缩文件哈希和解压文件哈希关系
class AZipFile:
    def __init__(self,path):
        self.path=path
        self.zipFile=AFile()
        self.unzipFileList=FileList()
        self.error=False

        self.get(path)
        
    def get(self,path):
        zipcount=0
        dircount=0
        
        inZipDir=os.listdir(self.path)
        #检查数据是否能匹配
        for i in inZipDir:
            p=os.path.join(path,i)
            q=p.lower()
            if q.endswith(".zip") or q.endswith(".rar") or q.endswith(".7z"):
                zipcount=zipcount+1
            if os.path.isdir(p):
                dircount=dircount+1                
        #数据错误处理
        if not zipcount==1:
            string=""
            string=string+self.path+"[more zip file] has more than one zip file, which is "+str(zipcount)
            Log.writeLog(string)
            self.error=True
            return
        
        fileList=[]

        #获取数据
        for i in inZipDir:
            p=os.path.join(path,i)
            q=p.lower()
            if q.endswith(".zip") or q.endswith(".rar") or q.endswith(".7z"):
                hash=getAHash(p)
                self.zipFile.hashMd5=hash
                self.zipFile.nowPath=p
            else:
                hash=GeneHash()
                hashList=hash.run(p)
                fileList.append(hashList)
        #对比多次解压的内容是否相同    
        for i in range(1,dircount):
            self.compare(fileList[0],fileList[i])
        #提取解压文件的哈希值    
        self.unzipFileList=fileList[0]

    #判别两个文件夹中的文件是否完全一致            
    def compare(self,a:FileList,b:FileList):
        a.sortByHash()
        b.sortByHash()
        if not len(a.fileList)==len(b.fileList):
            string="there is an error in \""+self.path+"\" please check"
            Log.writeLog("[zip or unzip error]"+string)
            self.error=True
        for i in range(0,len(a.fileList)):
            if a.fileList[i].hashMd5!=b.fileList[i].hashMd5:
                string="there is an error in \""+self.path+"\" please check"
                Log.writeLog("[zip or unzip error]"+string)
                self.error=True
                break
    
    def hasHash(self,hash):
        if self.zipFile[0]==hash:
            return True
        i:AFile
        for i in self.unzipFileList:
            if i.hashMd5==hash:
                return True
        return False     
    
    def __str__(self) -> str:
        string=""
        if self.error:
            string=string+"there is an error in "+self.path+" please check\n"
        else:
            string=string+"zipFile:\t"+self.zipFile.hashMd5+"\t"+self.zipFile.nowPath+"\n"
            for i in self.unzipFileList:
                string=string+"unzipFile:\t"+i.hashMd5+"\t"+i.nowPath+"\n"
        return string
    
    