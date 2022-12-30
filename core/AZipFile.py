import os
from log import *
from generateHash import *

class AZipFile:
    
    def __init__(self,path) -> None:
        self.path=path
        self.zipHash=""
        self.fileList=[]
        self.zipcount=0
        self.filecount=0
        self.error=False
        
        self.get()
        
    def get(self):
        
        inzipFile=os.listdir(self.path)
        
        #检查数据是否能匹配
        for i in inzipFile:
            p=os.path.join(self.path,i)
            if p.endswith(".zip") or p.endswith(".rar") or p.endswith(".7z"):
                self.zipcount=self.zipcount+1
            if os.path.isdir(p):
                self.filecount=self.filecount+1
                
        #数据错误处理
        if not self.zipcount==1:
            string=""
            string=string+self.path+" has more than one zip file"
            log.printLog(string)
            self.error=True
            return
        
        #获取数据
        for i in inzipFile:
            p=os.path.join(self.path,i)
            if p.endswith(".zip") or p.endswith(".rar") or p.endswith(".7z"):
                self.zipHash=GeneHash(p).fileList.fileList[0].hashMd5
            else:
                hash=GeneHash()
                hashList=hash.start(p)
                self.fileList.append(hashList)
            
        for i in range(1,self.filecount):
            self.compare(self.fileList[0],self.fileList[i])
                    
    def compare(self,a,b):
        for i in a:
            hasSame=False
            for j in b:
                if i==j:
                    hasSame=True
                    break
            if hasSame==False:
                self.error=True
                break
        return self.error
            
    def __str__(self) -> str:
        string=""
        if self.error:
            string="there is an error in "+self.path+" please check"
        else:
            string=string+self.zipHash+"\n"
            for i in self.fileList[0]:
                string=string+i.hashMd5+"\n"
        return string
    
if __name__=="__main__":
    path=input("请输入文件路径")
    path=os.path.abspath(path)
    print(path)
    zipfile=AZipFile(path)
    print(zipfile)
    