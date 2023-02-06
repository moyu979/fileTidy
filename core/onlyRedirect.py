import os
from RemoveFile import *
class onlyRedirect:
    def __init__(self) -> None:
        self.logfile=open("./onlyredirect.txt","w")
        pass
    def get(self,path):
        #print("check:"+path)
        #文件的话直接返回
        if not os.path.isdir(path):
            return 
        plist=os.listdir(path)
        #仅有redirect 记录
        if len(plist)==1 and plist[0]=="redirect.txt":
            self.logfile.write(path+"\n")
            remove(path)
            return
        else:
            for i in plist:
                np=os.path.join(path,i)
                self.get(np)

if __name__=="__main__":
    o=onlyRedirect()
    p=input("请输入目录")
    o.get(p)
        