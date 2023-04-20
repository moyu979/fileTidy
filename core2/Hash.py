from genericpath import isdir
import hashlib
from _FileList import *
import sys
#用于计算一个文件夹下所有文件的哈希值，返回一个记载所有文件信息的FileList(不去重)
class GeneHash:
    def __init__(self):        
        self.fileList=FileList()
        
        self.totalSize:float=0
        self.finished:float=0
    

    def run(self,path)->FileList:
        if type(path).__name__=='list':
            self.getListSize(path)
            self.listHash(path)
        elif type(path).__name__=='str':
            if(os.path.isdir(path)):
                self.getDirSize(path)
                self.dirHash(path)
            else:
                self.getFileSize(path)
                self.fileHash(path)
        else:
            return None
        return self.fileList

    def getListSize(self,path):
        for i in path:
            self.calTotalSize(i)
        print("total size: "+self.humanSize(self.totalSize))
    def listHash(self,path):
        for i in path:
            self.dirHash(i)

    def getDirSize(self,path):
        self.calTotalSize(path)
        print("total size: "+self.humanSize(self.totalSize))
    def dirHash(self,path):
        if(os.path.isdir(path)):
            for i in os.listdir(path):
                newPath=os.path.join(path,i)
                self.dirHash(newPath)
        else:
            self.fileHash(path)   

    def getFileSize(self,path):
        self.calTotalSize(path)
        print("total size: "+self.humanSize(self.totalSize))
    def fileHash(self,path):
        if(path.endswith("redirect.txt")):
            return
        md5=getAHash(path)
        file=AFile()
        file.hashMd5=md5
        file.changePath.append(path)
        file.originPath.add(path)
        file.autoupdate()
        self.fileList.append(file)
        self.finished=self.finished+os.path.getsize(path)
        self.showProgress()    

    def showProgress(self):
        print("\r nowfinish %f" % (self.finished/self.totalSize),flush=True,end="")    
        
    def calTotalSize(self,file)->float:
        if os.path.isdir(file):
            for i in os.listdir(file):
                j=os.path.join(file,i)
                self.calTotalSize(j)
        else:
            self.totalSize=self.totalSize+os.path.getsize(file)
            
    def humanSize(self,count:float)->str:
        size=["B","K","M","G","T"]
        sizelable=0
        while count>1024 and sizelable<5:
            count=count/1024
            sizelable=sizelable+1
        return "%.2f%s" % (count, size[sizelable])
    
def getAHash(path):
    if os.path.isdir(path):
        return None
    else:
        md5=hashlib.md5()
        with open(path,"rb") as fp:
            while True:
                data=fp.read(1024**3)
                if not data:
                    break
                md5.update(data)
        file_md5=md5.hexdigest()
        return file_md5
        
if __name__ == "__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入要计算哈希的文件或文件夹")
    path=os.path.abspath(path)
    res=GeneHash().run(path)
    print("777")
    print(len(res.fileList))
    res.print()