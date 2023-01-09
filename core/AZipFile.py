import os
from Hash import *
import Log


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
            string=string+self.path+" has more than one zip file, which is "+str(zipcount)
            Log.printLog(string)
            self.error=True
            return
        
        fileList=[]
        #获取数据
        for i in inzipFile:
            p=os.path.join(path,i)
            if p.endswith(".zip") or p.endswith(".rar") or p.endswith(".7z"):
                self.zipHash=[GeneHash(p).fileList.fileList[0].hashMd5,GeneHash(p).fileList.fileList[0].nowPath]
            else:
                hash=GeneHash()
                hashList=hash.start(p)
                fileList.append(hashList)
        #对比多次解压的内容是否相同    
        for i in range(1,dircount):
            self.compare(fileList[0],fileList[i])
        #提取解压文件的哈希值    
        for i in fileList[0]:
            self.fileList.append([i.hashMd5,i.nowPath])    
    #判别两个文件夹中的文件是否完全一致            
    def compare(self,a:FileList,b:FileList):
        for i in a:
            hasSame=False
            for j in b:
                if i.hashMd5==j.hashMd5:
                    print("found")
                    hasSame=True
                    b.deleteByHash(j.hashMd5)
                    a.deleteByHash(j.hashMd5)
                    break
            if hasSame==False:
                self.error=True
                break
        if len(a.fileList)!=0 or len(b.fileList)!=0:
            self.error=True
        return self.error
    def hasHash(self,hash):
        if self.zipHash==hash:
            return True
        for i in self.fileList:
            if i[0]==hash:
                return True
        return False     
    def __str__(self) -> str:
        string=""
        if self.error:
            string="there is an error in "+self.path+" please check"
        else:
            string=string+self.zipHash+"\n"
            for i in self.fileList:
                string=string+i[0]+"::"+i[1]+"\n"
        return string
    
if __name__=="__main__":
    path=input("请输入文件路径")
    path=os.path.abspath(path)
    print(path)
    zipfile=AZipFile(path)
    print(zipfile)
    