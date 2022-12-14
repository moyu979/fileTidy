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
            if aline.startswith("end\n"):
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
        #如果找到了不相同的重复文件
        if sameFile:
            #同一个文件，直接返回
            if sameFile.nowPath==a.nowPath:
                return False
            elif compareFile(sameFile.nowPath,a.nowPath):
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
   
                
    #输出
    def outPut(self,path):
        count=0
        outFile=open(path,'w',encoding="utf-8")
        for i in self.fileList:
            outFile.write("num:\t"+str(count)+"\n")
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
        if self.itercount==len(self.fileList):
            raise StopIteration
        else:
            self.itercount=self.itercount+1
            return self.fileList[self.itercount-1]
if __name__ == "__main__":
    print ("这是一个基础数据单元，不能作为运行单元")