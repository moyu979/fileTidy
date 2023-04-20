import os.path
from Log import *
from HashSet import *
#AFile 模块，作为基本单元而存在，在不同函数之间传递消息通常使用这个
class AFile:
    def __init__(self,paras:str=None) -> None:
        #特征组
        self.hashMd5=None
        self.sameHashCount=0
        self.removed=False
        self.lossFile=False
        self.noSourceFile=False
        #初始目录组
        #此组至少有一个不为空，举例而言
        ##当解压来的文件，unzip不为空
        ##压缩来的文件，zip不为空
        ##普通下载来的文件，originpath不为空
        self.originPath=set()
        self.unzipFrom=set()
        self.zipFrom=set()
        #变化组
        self.changePath=[]
        #现状组
        #如果removed为真，此文件处于被删除状态，则现在的路径和文件名皆为空
        self.nowName=None
        self.nowPath=None

        #遍历字段
        self.visited=False
        if paras!=None:
            self.loadFile(paras)
    #使用字符串构造一个变量        
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
            if plist[0] == 'lossFile':
                self.lossFile=True  
            if plist[0] == 'noSourceFile':
                self.noSourceFile=True    
        #来源        
            #原始目录项
            if plist[0] == 'originPath':
                self.originPath.add(plist[1])
            #相同项(历史遗留)
            if plist[0] == 'sameAs':
                self.originPath.add(plist[1])
            #解压自
            if plist[0] == 'unzip':
                self.unzipFrom.add(plist[1])
            if plist[0] == 'unzipFrom':
                self.unzipFrom.add(plist[1])
            #压缩到
            if plist[0] == 'zip':
                self.zipFrom.add(plist[1])
            if plist[0] == 'zipFrom':
                self.zipFrom.add(plist[1])
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
        if not self.removed:
            self.nowPath=self.changePath[-1]
            self.nowName=os.path.basename(self.nowPath)
    #     if len(self.changePath)==0:
    #         for i in self.originPath:
    #             if os.path.exists(i):
    #                 self.changePath.append(i)
    #     if len(self.changePath)==0:
    #             for i in self.originPath:       
    #                 self.changePath.append(i)
    #                 break 
    #     #如果没被删除的话，自动生成现在的路径什么的
    #     if not self.removed and not self.noSourceFile:
    #         #将变化目录的最后一个（最近日期的目录）或原始目录（没有变化）视作现在的目录
    #         if len(self.changePath)==0:
    #             pass
    #         else:
    #             self.nowPath=self.changePath[-1]
    #         #从现在的目录中提取出文件名
    #         self.nowName=os.path.basename(self.nowPath)
    
    #字符串
    def __str__(self,adds="") -> str:
        self.autoupdate()
        string=""
        string=string+adds
        string=string+"hashMd5:\t"+self.hashMd5+"\n"
        if self.sameHashCount!=0:
            string=string+"sameHashCount:\t"+str(self.sameHashCount)+"\n"
        if self.noSourceFile:
            string=string+"noSourceFile\n"
        if self.lossFile:
            string=string+"lossFile\n"
        if self.removed:
            string=string+"removed\n"
        else:
            string=string+"nowName:\t"+self.nowName+"\n"
            string=string+"nowPath:\t"+self.nowPath+"\n"
        
        #保证set的顺序
        temp=[]
        for i in self.originPath:
            temp.append(i)
        temp.sort()
        for i in temp:
            string=string+"originPath:\t"+i+"\n"

        
        temp=[]
        for i in self.unzipFrom:
            temp.append(i)
        temp.sort()
        for i in temp:
            string=string+"unzipFrom:\t"+i+"\n"

                
            
        temp=[]
        for i in self.zipFrom:
            temp.append(i)
        temp.sort()
        for i in temp:
            string=string+"zipFrom:\t"+i+"\n"
               
        for i in self.changePath:
            string=string+"changePath:\t"+i+"\n"

        string=string+"end\n"
        return string

