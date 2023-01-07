import os.path
from Log import *
#AFile 模块，作为基本单元而存在，在不同函数之间传递消息通常使用这个
class AFile:
    def __init__(self,paras:str=None) -> None:
        #特征组
        self.hashMd5=None
        self.sameHashCount=0
        self.removed=False
        #初始目录组
        #此组至少有一个不为空，举例而言
        ##当解压来的文件，unzip不为空
        ##压缩来的文件，zip不为空
        ##普通下载来的文件，originpath不为空
        self.originPath=set()
        self.unzip=set()
        self.zip=set()
        #变化组
        self.changePath=[]
        #现状组
        #如果removed为真，此文件处于被删除状态，则现在的路径和文件名皆为空
        self.nowName=None
        self.nowPath=None

        
        if paras!=None:
            self.loadFile(paras)
            
    def loadFile(self,paras:str):    
        for para in paras:
            #去除换行符并切分
            p=para.replace("\n","")
            plist=p.split(":\t")
        #唯一标记
            #md5纪录项(唯一)
            if plist[0] == 'hashMd5':
                self.hashMd5=plist[1]
            #处理减少哈希冲突的
            if plist[0] == 'sameHashCount':
                self.sameHashCount=int(plist[1])
            #是否已经被删除
            if plist[0] == 'removed':
                self.removed=True    
        #来源        
            #原始目录项
            if plist[0] == 'originPath':
                self.originPath.add(plist[1])
            #相同项(历史遗留)
            if plist[0] == 'sameAs':
                self.originPath.add(plist[1])
            #解压自
            if plist[0] == 'unzip':
                self.unzip.add(plist[1])
            if plist[0] == 'unzipFrom':
                self.unzip.add(plist[1])
            #压缩到
            if plist[0] == 'zip':
                self.zip.add(plist[1])
            if plist[0] == 'zipFrom':
                self.zip.add(plist[1])
        #常用数据            
            #现在路径
            if plist[0] == 'nowPath':
                self.nowPath=plist[1]  
            #路径变迁
            if plist[0] == 'changePath':
                self.changePath.append(plist[1])
        #自动更新一下
        self.autoupdate()
        
    #自动更新 
    def autoupdate(self):
        if len(self.changePath)==0:
            for i in self.originPath:
                self.changePath.append(i)
        #如果没被删除的话，自动生成现在的路径什么的
        if not self.removed:
            #将变化目录的最后一个（最近日期的目录）或原始目录（没有变化）视作现在的目录
            if len(self.changePath)==0:
                pass
            else:
                self.nowPath=self.changePath[-1]
            #从现在的目录中提取出文件名
            self.nowName=os.path.basename(self.nowPath)
    
    #字符串
    def __str__(self,adds="") -> str:
        self.autoupdate()
        string=""
        string=string+adds
        string=string+"hashMd5:\t"+self.hashMd5+"\n"
        if self.sameHashCount!=0:
            string=string+"sameHashCount:\t"+str(self.sameHashCount)+"\n"
        if self.removed:
            string=string+"removed\n"
        else:
            if self.nowName:
                string=string+"nowName:\t"+self.nowName+"\n"
            if self.nowPath:
                string=string+"nowPath:\t"+self.nowPath+"\n"

        for i in self.originPath:
            string=string+"originPath:\t"+i+"\n"
        for i in self.unzip:
            string=string+"unzipFrom:\t"+i+"\n"
        for i in self.zip:
            string=string+"zipFrom:\t"+i+"\n"
            
        for i in self.changePath:
            string=string+"changePath:\t"+i+"\n"

        string=string+"end\n"
        return string
    #增加内容
    #添加zip内容
    def addZip(self,zip):
        if type(zip).__name__=="str":
            self.zip.add(zip)
        elif type(zip).__name__=="set":
            self.zip=self.zip|zip
        elif type(zip).__name__=="list":
            for i in zip:
                self.zip.add(i)
        else:
            error="unknown type while combine zip of \""+self.hashMd5+" "+self.nowName+" \" "
            writeLog(error)
            
    def addUnzip(self,unzip):
        if type(unzip).__name__=="str":
            self.unzip.add(unzip)
        elif type(unzip).__name__=="set":
            self.unzip=self.unzip|unzip
        elif type(unzip).__name__=="list":
            for i in unzip:
                self.unzip.add(i)
        else:
            error="unknown type while combine Unzip of \""+self.hashMd5+" "+self.nowName+" \" "
            writeLog(error)
            
    def addOriginPath(self,originPath):
        if type(originPath).__name__=="str":
            self.originPath.add(originPath)
        elif type(originPath).__name__=="set":
            self.originPath=self.originPath|originPath
        elif type(originPath).__name__=="list":
            for i in originPath:
                self.originPath.add(i)
        else:
            error="unknown type while combine OriginPath of \""+self.hashMd5+" "+self.nowName+" \" "
            writeLog(error)
            
    def addChangePath(self,changePath):
        if type(changePath).__name__=="str":
            self.changePath.append(changePath)
        elif type(changePath).__name__=="list":
            for i in changePath:
                self.changePath.append(i)
        else:
            error="unknown type while combine changePath of \""+self.hashMd5+" "+self.nowName+" \" "
            writeLog(error)
            
    #将两个具有相同哈希值的合并
    def combinewith(self,A):
        if A.hashMd5!=None and self.hashMd5!=A.hashMd5:
            return False
        else:
            self.addOriginPath(A.originPath)
            self.addUnzip(A.unzip)
            self.addZip(A.zip)
            self.addChangePath(A.changePath)
            if A.removed:
                self.removed=True

if __name__ == "__main__":
    print ("这是一个基础数据单元，不能作为运行单元")