import hashlib
import os
import sys
from _processManage import *
class Hash:
    def __init__(self):
        self.fileList=[]
        self.sizeManage=None
        self.showProgress=False

    def __call__(self,path,showProgress=True)->list:
        self.showProgress=showProgress
        if self.showProgress:
            self.sizeManage=sizeManage(path)
        if type(path).__name__=='list':
            for i in path:
                self.dirHash(i)
        elif type(path).__name__=='str':
            if(os.path.isdir(path)):
                self.dirHash(path)
            else:
                self.fileHash(path)
        else:
            return None
        return self.fileList

    def dirHash(self,path):
        if(os.path.isdir(path)):
            for i in os.listdir(path):
                newPath=os.path.join(path,i)
                self.dirHash(newPath)
        else:
            self.fileHash(path)

    def fileHash(self,path):
        md5=getAHash(path)
        self.fileList.append([md5,path])
        if self.showProgress:
            self.sizeManage.update(path)
            self.sizeManage.showProgress()

def getAHash(path,size=512):
    if os.path.isdir(path):
        return None
    else:
        md5=hashlib.md5()
        with open(path,"rb") as fp:
            while True:
                data=fp.read(1024**2*size)
                if not data:
                    break
                md5.update(data)
        file_md5=md5.hexdigest()
        return file_md5
    
if __name__=="__main__":
    path=""
    if len(sys.argv)!=2:
        path=input("请输入测试路径")
    else:
        path=sys.argv[1]
    path=os.path.abspath(path)
    path=path.replace("\\","/")
    h=Hash()
    h(path)
    h.show()
    