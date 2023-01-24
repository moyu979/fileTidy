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
            self.start(path)
            
    def start(self,file)->FileList:
        file=os.path.abspath(file)
        self.totalSize=self.takeSizes(file)
        print("total size: "+self.humanSize(self.totalSize))
        self.geneHash(file)
        print("\n")
        return self.fileList
    #传入列表，计算列表的哈希
    def startFileList(self,lists):
        for i in lists:
            self.totalSize=self.totalSize+os.path.getsize(i)
        print("total size: "+self.humanSize(self.totalSize))
        for i in lists:
            self.geneHash(i)
            print("\r nowfinish %f" % (self.finished/self.totalSize),flush=True,end="")
            
    def humanSize(self,count:float)->str:
        size=["B","K","M","G","T"]
        sizelable=0
        while count>1024 and sizelable<5:
            count=count/1024
            sizelable=sizelable+1
        return "%.2f%s" % (count, size[sizelable])
    
    def takeSizes(self,file)->float:
        count:float=0
        if os.path.isdir(file):
            for i in os.listdir(file):
                j=os.path.join(file,i)
                count=count+self.takeSizes(j)
        else:
            count=count+os.path.getsize(file)
        return count
    
    def geneHash(self,file):
        if self.totalSize==0:
            return FileList()
        print("\r nowfinish %f" % (self.finished/self.totalSize),flush=True,end="")
        af=[]
        if os.path.isdir(file):
            for i in os.listdir(file):
                j=os.path.join(file,i)
                self.geneHash(j)
        else:
            #忽略掉所有的redirect文件
            if os.path.basename(file)=="redirect.txt":
                return
            filesize=os.path.getsize(file)
            if filesize>1024**3:
                md5=hashlib.md5()
                with open(file,"rb") as fp:
                    while True:
                        data=fp.read(1024**3)
                        if not data:
                            break
                        md5.update(data)
                file_md5=md5.hexdigest()
                af.append("hashMd5:\t"+file_md5)
                af.append("originPath:\t"+file)
                af.append("changePath:\t"+file)
                af.append("nowPath:\t"+file)
                af.append("end\n")
            else:
                with open(file,"rb") as fp:
                    data=fp.read()
                file_md5=hashlib.md5(data).hexdigest()
                af.append("hashMd5:\t"+file_md5)
                af.append("originPath:\t"+file)
                af.append("changePath:\t"+file)
                af.append("nowPath:\t"+file)
                af.append("end\n")
            f=AFile(af)
            self.fileList.fileList.append(f)
            self.finished=self.finished+filesize
    
if __name__ == "__main__":
    print("这个模块不会产生可存储输出，只会将结果输出到控制台，是否继续？")
    yon=input()
    if yon.startswith("y"):
        print("好吧，请输入路径")
        path=input()
        path=os.path.abspath(path)
        c=GeneHash()
        list=c.start(path)
        list.pOutPut()