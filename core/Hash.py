from genericpath import isdir
import hashlib
from FileList import *

#用于计算一个文件夹下所有文件的哈希值，返回一个记载所有文件信息的FileList(不去重)
class GeneHash:
    def __init__(self,path=None):
        
        self.fileList=FileList()
        
        self.totalSize:float=0
        self.finished:float=0
        
        if path:
            self.run(path)
    
    def run(self,path)->FileList:
        if type(path).__name__=='list':
            for i in path:
                self.totalSize=self.totalSize+self.calTotalSize(i)
            print("total size: "+self.humanSize(self.totalSize))
            self.listHash(path)
        elif type(path).__name__=='str':
            if(os.path.isdir(path)):
                self.totalSize=self.calTotalSize(path)
                print("total size: "+self.humanSize(self.totalSize))
                self.dirHash(path)
            else:
                self.fileHash(path)
        else:
            return None
        print("")
        return self.fileList
    
    def listHash(self,path):
        for i in path:
            self.dirHash(i)
            
    def fileHash(self,path):
        if(path.endswith("redirect.txt")):
            return
        md5=getAHash(path)
        file=AFile()
        file.hashMd5=md5
        file.changePath.append(path)
        file.originPath.add(path)
        file.autoupdate()
        self.fileList.fileList.append(file)
        if self.totalSize!=0:
            self.finished=self.finished+os.path.getsize(path)
            print("\r nowfinish %f" % (self.finished/self.totalSize),flush=True,end="")
    
    def dirHash(self,path):
        if(os.path.isdir(path)):
            for i in os.listdir(path):
                newPath=os.path.join(path,i)
                self.dirHash(newPath)
        else:
            self.fileHash(path)
        
        
    def calTotalSize(self,file)->float:
        count:float=0
        if os.path.isdir(file):
            for i in os.listdir(file):
                j=os.path.join(file,i)
                count=count+self.calTotalSize(j)
        else:
            count=count+os.path.getsize(file)
        return count
            
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
    res.print()