import os.path
import log
#记录文件结构的数据项
class AFile:
    def __init__(self,paras:str) -> None:
        #特征组
        self.hashMd5=None
        #初始目录组
        self.originPath=[]
        self.unzip=[]
        self.zip=[]
        #变化组
        self.changePath=[]
        #现状组
        self.nowName=None
        self.nowPath=None
        self.removed=False
        
        for para in paras:
            plist=para.split(":\t")
            #md5纪录项(唯一)
            if plist[0] == 'hashMd5':
                self.hashMd5=plist[1]
            #原始目录项
            if plist[0] == 'originPath':
                self.originPath.append(plist[1])
            #相同项(历史遗留)
            if plist[0] == 'sameAs':
                self.originPath.append(plist[1])
            #路径变迁
            if plist[0] == 'changePath':
                self.changePath.append(plist[1])
            #解压自
            if plist[0] == 'unzipFrom':
                self.unzip.append(plist[1])
            #压缩到
            if plist[0] == 'zipTo':
                self.zip.append(plist[1])
            if plist[0] == 'removed':
                self.removed=True
                
            if plist[0] == 'num':
                pass

        if len(self.changePath)==0:
            self.nowPath = self.originPath[0]
        else:
            self.nowPath=self.changePath[-1]

        self.nowName=os.path.basename(self.nowPath)

    def __str__(self,adds="") -> str:
        string=""
        string=string+adds
        string=string+"hashMd5:\t"+self.hashMd5
        string=string+"nowName:\t"+self.nowName
        string=string+"nowPath:\t"+self.nowPath

        for i in self.originPath:
            string=string+"originPath:\t"+i

        for i in self.changePath:
            string=string+"changePath:\t"+i

        for i in self.unzip:
            string=string+"unzip:\t"+i

        for i in self.zip:
            string=string+"zip:\t"+i

        if self.removed:
            string=string+"removed\n"
            
        string=string+"end\n"
        return string

    def insertOriginPath(self,ori):
        if type(ori).__name__=="str":
            for i in self.originPath:
                if i==ori:
                    return
            self.originPath.append(ori)
        elif type(ori).__name__=="list":
            for j in ori:
                for i in self.originPath:
                    if i==j:
                       break
                self.originPath.append(j)
        else:
            l=[]
            l.append("未知的参数类型\n")
            l.append("计划将类型为"+type(ori).__name__+"的参数写入\n")
            l.append("将内容："+ori.__str__+"\t写入:"+self.hashMd5+"\t中originPath的项\n")
            log.write(l)
            
    def insertunzip(self,ori):
        if type(ori).__name__=="str":
            for i in self.unzip:
                if i==ori:
                    return
            self.unzip.append(ori)
        elif type(ori).__name__=="list":
            for j in ori:
                for i in self.unzip:
                    if i==j:
                        break
                self.unzip.append(j)
        else:
            l=[]
            l.append("未知的参数类型\n")
            l.append("计划将类型为"+type(ori).__name__+"的参数写入\n")
            l.append("将内容："+ori.__str__+"\t写入:"+self.hashMd5+"\t中unzip的项\n")
            log.write(l)
            
    def insertzip(self,ori):
        if type(ori).__name__=="str":
            for i in self.zip:
                if i==ori:
                    return
            self.zip.append(ori)
        elif type(ori).__name__=="list":
            for j in ori:
                for i in self.zip:
                    if i==j:
                        break
                self.zip.append(j)
        else:
            l=[]
            l.append("未知的参数类型\n")
            l.append("计划将类型为"+type(ori).__name__+"的参数写入\n")
            l.append("将内容："+ori.__str__+"\t写入:"+self.hashMd5+"\t中zip的项\n")
            log.write(l)
            
    def insertremoved(self,ori):
        if type(ori).__name=="bool":
            if self.removed and not ori:
                self.removed=False
        else:
            l=[]
            l.append("未知的参数类型\n")
            l.append("计划将类型为"+type(ori).__name__+"的参数写入\n")
            l.append("将内容："+ori.__str__+"\t写入:"+self.hashMd5+"\t中remove的项\n")
            log.write(l)
                   
if __name__ == "__main__":
    print ("这是一个基础数据单元，不能作为运行单元")