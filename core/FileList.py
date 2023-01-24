from AFile import *
from CompareFile import *
from RemoveFile import *
import Log

#排序用函数
def return_now_path(elem:AFile):
    return elem.nowPath
def return_now_name(elem:AFile):
    return elem.nowName
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
            if aline.startswith("end") or aline=="\n":
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
        inFile.close()
    #排序        
    def sortBypath(self):
        self.fileList.sort(key=return_now_path)
        
    def sortByHash(self):
        self.fileList.sort(key=return_hash)
        
    def sortByName(self):
        self.fileList.sort(key=return_now_name)
        
    #增
    ##增加一个文件(去重),有重返回True
    def addAFile(self,a:AFile): 
        sameFile=self.findHash(a.hashMd5)
        #如果找到了不相同的重复文件
        if sameFile:
            #同一个文件，直接返回
            if sameFile.nowPath==a.nowPath:
                return False
            #两个文件相同 直接combine
            elif compareFile(sameFile.nowPath,a.nowPath):
                sameFile.originPath=sameFile.originPath|a.originPath
                sameFile.zipFrom=sameFile.zipFrom|a.zipFrom
                sameFile.unzipFrom=sameFile.unzipFrom|a.unzipFrom
                return True
            #找到了相同的哈希，但文件内容不同
            #或者旧文件被删除了也会产生此错误
            else:
                log=Log()
                string="[hash conflication]find files with same hash but not same \n"+"first is:"+sameFile.nowPath
                string=string+"\n"+"second is:"+a.nowPath+"\n"
                Log.printAndLog(string)
                return False
        else:
            self.fileList.append(a)
            return False
        
    ##将一个FileList添加到现有的FileList中，如果遇到相同的，不合并，而是将新旧两个文件进记录到findsame列表下，等待进一步处理
    def combine(self,files):
        findsame=[]
        files.sortBypath()
        for i in files:
            if self.addAFile(i):
                findsame.append(i)
        return findsame
    
    #删
    def deleteByHash(self,Hash):
        i:AFile
        for i in self.fileList:
            if i.hashMd5==Hash:
                self.fileList.remove(i)
                self.itercount=self.itercount-1
                
    def deleteByNowPath(self,path):
        i:AFile
        for i in self.fileList:
            if i.nowPath==path:
                self.fileList.remove(i)
                self.itercount=self.itercount-1            
    #改
    def removeAFile(self,Hash):
        i:AFile
        for i in self.fileList:
            if i.hashMd5==Hash:
                i.removed=True
                            
    #查
    def findHash(self,hash)->AFile:
        for i in self.fileList:
            if i.hashMd5==hash:
                return i
        return None

    def findPath(self,path)->AFile:
        for i in self.fileList:
            if i.nowPath==path:
                return i
        return None
    
    #输出
    def outPut(self,path):
        #self.sortBypath()
        count=1
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
    #重置遍历标志：
    def resetVisit(self):
        i:AFile
        for i in self.fileList:
            i.visited=False
        #重写迭代器
    def __iter__(self):
        self.itercount=0
        return self
    def __next__(self):
        if self.itercount>=len(self.fileList):
            raise StopIteration
        else:
            self.itercount=self.itercount+1
            return self.fileList[self.itercount-1]
        
if __name__ == "__main__":
    print ("这是一个基础数据单元，不能作为运行单元,当运行时，会读入并原样输出列表（主要用于列表的升级）")
    path=input("请输入列表地址")
    fileList=FileList()
    fileList.importFileList(path)
    
    path2=input("请输入输出地址")
    fileList.outPut(path2)