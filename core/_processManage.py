import os
import sys
from time import sleep
class ProcessManage:
    def __init__(self,path) -> None:
        self.totalSize:float=0
        self.finished:float=0
        self.temp=0

        self.totalSize=self.calSize(path)
        self.show=True
        print("total size: "+self.humanSize(self.totalSize))
        
    def update(self,path):
        self.calSize(path)
        self.finished=self.finished+self.temp
        if self.show:
            self.showProgress()

    def showProgress(self):
        print("\r nowfinish %f " % (self.finished/self.totalSize),flush=True,end="")   
        
    def calSize(self,path)->float:
        self.temp=0
        if type(path).__name__=='list':
            for i in path:
                self.calTotalSize(i)
        elif type(path).__name__=='str':
            self.calTotalSize(path)
        return self.temp
    
    def calTotalSize(self,file)->float:
        if os.path.isdir(file):
            for i in os.listdir(file):
                j=os.path.join(file,i).replace("\\","/")
                self.calTotalSize(j)
        else:
            self.temp=self.temp+os.path.getsize(file)

    def humanSize(self,count:float)->str:
        size=["B","K","M","G","T"]
        sizelable=0
        while count>1024 and sizelable<5:
            count=count/1024
            sizelable=sizelable+1
        return "%.2f%s" % (count, size[sizelable])
    
if __name__=="__main__":
    if len(sys.argv)!=2:
        path=input("请输入测试位置")
    else:
        path=sys.argv[1]
    path=os.path.abspath(path)
    path=path.replace("\\","/")
    p=sizeManage(path)
    pl=os.listdir(path)
    for i in pl:
        p.update(i)
        p.showProgress()
        sleep(1)
        print()