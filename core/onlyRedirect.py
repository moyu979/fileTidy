import os
import sys
from core2.RemoveFile import *
class onlyRedirect:
    def __init__(self,path) -> None:
        self.logfile=open("./onlyredirect.txt","w")
        if path!=None:
            self.get(path)
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

if __name__ == "__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入要检查的文件或文件夹")
    path=os.path.abspath(path)
    onlyRedirect(path)