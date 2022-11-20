import os.path

class AFile:
    def __init__(self,paras:str) -> None:
        #特征组
        self.hashMd5=None
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
        self.removed=False
        
        for para in paras:
            p=para.replace("\n","")
            plist=p.split(":\t")
            #md5纪录项(唯一)
            if plist[0] == 'hashMd5':
                self.hashMd5=plist[1]
            #原始目录项
            if plist[0] == 'originPath':
                self.originPath.add(plist[1])
            #相同项(历史遗留)
            if plist[0] == 'sameAs':
                self.originPath.add(plist[1])
            #解压自
            if plist[0] == 'unzip':
                self.unzip.add(plist[1])
            #压缩到
            if plist[0] == 'zip':
                self.zip.add(plist[1])
            #现在路径
            if plist[0] == 'nowPath':
                self.nowPath=plist[1]  
            #路径变迁
            if plist[0] == 'changePath':
                self.changePath.append(plist[1])
            if plist[0] == 'removed':
                self.removed=True
                
            
        #如果没被删除的话，自动生成现在的路径什么的
        if not self.removed:
            #将变化目录的最后一个（最近日期的目录）或原始目录（没有变化）视作现在的目录
            ##当没有任何的changePath的时候，说明原文件没有移动，因此直接保留即可，同时因为新加入的文件会重定位到新的文件上，所以无需担心新文件将老文件踢掉
            if len(self.changePath)==0:
                pass
            else:
                self.nowPath=self.changePath[-1]
            #从现在的目录中提取出文件名
            self.nowName=os.path.basename(self.nowPath)
    #字符串
    def __str__(self,adds="") -> str:
        
        string=""
        string=string+adds
        string=string+"hashMd5:\t"+self.hashMd5+"\n"
        if self.removed:
            string=string+"removed\n"
        if self.nowName:
            string=string+"nowName:\t"+self.nowName+"\n"
        if self.nowPath:
            string=string+"nowPath:\t"+self.nowPath+"\n"

        for i in self.originPath:
            string=string+"originPath:\t"+i+"\n"

        for i in self.changePath:
            string=string+"changePath:\t"+i+"\n"

        for i in self.unzip:
            string=string+"unzip:\t"+i+"\n"

        for i in self.zip:
            string=string+"zip:\t"+i+"\n"

        string=string+"end\n"
        return string
    
    def resetHash(self,newHash):
        self.hashMd5=newHash
    #增加内容
    def addZip(self,zip):
        if type(zip).__name__=="str":
            self.zip.add(zip)
        elif type(zip).__name__=="set":
            self.zip=self.zip|zip
    def addUnzip(self,unzip):
        if type(unzip).__name__=="str":
            self.unzip.add(unzip)
        elif type(unzip).__name__=="set":
            self.unzip=self.unzip|unzip
    def addOriginPath(self,originPath):
        if type(originPath).__name__=="str":
            self.originPath.add(originPath)
        elif type(originPath).__name__=="set":
            self.originPath=self.originPath|originPath

if __name__ == "__main__":
    print ("这是一个基础数据单元，不能作为运行单元")