import hashlib
import os
import sys
from _processManage import *

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
