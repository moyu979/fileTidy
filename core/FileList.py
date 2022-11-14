from AFile import *
from compareFile import *
from removeSameFile import *

#排序用函数
def return_now_path(elem:AFile):
    return elem.nowPath
def return_hash(elem:AFile):
    return elem.hashMd5

class FileList:
    #初始化
    def __init__(self,path=None) -> None:
        self.itercount=0
        self.fileList=[]
        #如果参数有path的话使用path初始化
        if not path==None:
            self.importFileList(path)
    #加载路径记录的文件        
    def importFileList(self,path):
        inFile=open(path,encoding="utf-8")
        af=[]
        aline:str=inFile.readline()
        while aline:
            #如果一行结束，增加一个文件
            if aline.startswith("end\n") or aline == "\n":
                if not af==[]:
                    self.fileList.append(AFile(af))
                af=[]
            #剥去filelist增加的辅助元素
            elif aline.startswith("num"):
                pass
            #增加行
            else:
                af.append(aline)
            #读新行
            aline=inFile.readline()
            
    #排序        
    def sortBypath(self):
        self.fileList.sort(key=return_now_path)
        
    def sortByHash(self):
        self.fileList.sort(key=return_hash)
    #增
    ##增加一个文件(去重),有重返回True
    def addAFile(self,a:AFile): 
        sameFile=self.findHash(a.hashMd5)
        if sameFile:
            if compareFile(sameFile.nowPath,a.nowPath):
                sameFile.addOriginPath(a.originPath)
                sameFile.addZip(a.zip)
                sameFile.addUnzip(a.unzip)
                return True
            else:
                count=0
                same=self.findHash(a.hashMd5+str(count))
                while(same):
                    if compareFile(same.nowPath,a.nowPath):
                        same.addOriginPath(a.originPath)
                        same.addZip(a.zip)
                        same.addUnzip(a.unzip)
                        return True
                    count=count+1    
                    same=self.findHash(a.hashMd5+str(count))
                a.hashMd5=a.hashMd5+str(count)
        self.fileList.append(a)
        return False
    ##将一个FileList添加到现有的FileList中，如果遇到相同的，不合并，而是将新旧两个文件进记录到findsame列表下，等待进一步处理
    def combine(self,files):
        findsame=[]
        if type(files).__name__=="list":
            fs=files
        elif type(files).__name__=="FileList" :
            fs=files.fileList
        for i in fs:
            if self.addAFile(i):
                findsame.append(i)
        return findsame
    
    #删
    def deleteByHash(self,Hash):
        i:AFile
        for i in self.fileList:
            if i.hashMd5==Hash:
                self.fileList.remove(i)
    #查
    def findHash(self,hash)->AFile:
        for i in self.fileList:
            if i.hashMd5==hash:
                return i
        return None
    #去重，不会删除
    # def takeofSame(self):
    #     length=len(self.fileList)
    #     sameList=[]
    #     i=0 
    #     j=0
    #     while(i<length):
    #         j=i+1
    #         while j<length:
    #             f1:AFile=self.fileList[i]
    #             f2:AFile=self.fileList[j]
    #             #有问题，只检查了一次哈希碰撞，没检查二次碰撞
    #             if f1.hashMd5==f2.hashMd5:
    #                 #是文件冲突而不是哈希碰撞
    #                 if compareFile(f1.nowPath,f2.nowPath):
    #                     del self.fileList[j]
    #                     j=j-1
    #                     length=length-1
    #                     sameList.append([f1,f2])
    #                 #哈希碰撞的情况
    #                 #这个是有问题的，没检查二次碰撞
    #                 else:
    #                     count=0
    #                     file=self.findHash(f2.hashMd5+str(count))
    #                     while file:
    #                         if compareFile(file.originPath,f2.originPath):
                                
    #                         count=count+1
    #                     f2.hashMd5=f2.hashMd5+str(count)
    #             j=j+1
    #         i=i+1
    #     return sameList         
                
    #输出
    def outPut(self,path):
        count=0
        outFile=open(path,'w',encoding="utf-8")
        for i in self.fileList:
            outFile.write("num:\t"+str(count))
            outFile.write(str(i))
            count=count+1
        outFile.flush()
        outFile.close()
    def pOutPut(self):
        for i in self.fileList:
            print(i)
            
    #重写迭代器
    def __iter__(self):
        self.itercount=0
        return self
    def __next__(self):
        if self.i==len(self.fileList):
            raise StopIteration
        else:
            self.i=self.i+1
            return self.fileList[self.i-1]
if __name__ == "__main__":
    print ("这是一个基础数据单元，不能作为运行单元")