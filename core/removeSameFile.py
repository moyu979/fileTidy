from AFile import *
import os
#将f2的文件删除，在原地的“redirect.txt”文件中记录
def removeFile(file2:AFile):
    file2Path=file2.nowPath
    file2Dir=file2.nowPath.replace(file2.nowName,"")
    redirPath=file2Dir+"redirect.txt"
    if os.path.exists(redirPath):
        fp=open(redirPath,"a",encoding="utf-8")
    else:
        fp=open(redirPath,"w",encoding="utf-8")
        fp.write(file2Dir)
        fp.write("\n")
        fp.write("\n")
    fp.write("hash:\t"+file2.hashMd5)
    fp.write("name:\t"+file2.nowName)
    fp.close()
    os.remove(file2Path)
    
    