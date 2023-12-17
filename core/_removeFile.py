import os
from _Log import *
import sys
#将f2的文件删除，在原地的“redirect.txt”文件中记录
def removeFile(filePath,hash):
    name=os.path.basename(filePath)

    fileDir=filePath.replace(name,"")
    redirPath=fileDir+"redirect.txt"

    #存在则打开，不存在则新建
    if os.path.exists(redirPath):
        fp=open(redirPath,"a",encoding="utf-8")
    else:
        fp=open(redirPath,"w",encoding="utf-8")
        fp.write(fileDir.replace("\\","/"))
        fp.write("\n")
        fp.write("\n")
        
    fp.write("hash:\t"+hash+"\n")
    fp.write("name:\t"+name+"\n")
    fp.close()

    Log.writeLog("[remove file]\tremove\t"+filePath.replace("\\","/")+"\twith hash\t"+hash)

    os.remove(filePath)
        
def removeFiles(files):
    for i in files:
        removeFile(i)
        
def removeAll(path):
    if os.path.isdir(path):
        list=os.listdir(path)
        for i in list:
            absp=os.path.join(path,i)
            removeAll(absp)
        os.rmdir(path)
    else:
        Log.writeLog("[remove file]\tremove\t"+path.replace("\\","/"))
        os.remove(path)
        
        
def removeEmpty(path):
    if not os.path.isdir(path):
        return
    else:
        list=os.listdir(path)
        for i in list:
            dir=os.path.join(path,i)
            removeEmpty(dir)
        list=os.listdir(path)
        if len(list)==0:
            os.rmdir(path)
            Log.writeLog("[remove empty]\tremove\t"+path+"\n")
            return
        
if __name__ == "__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入要检查的文件或文件夹")
    path=os.path.abspath(path)
    path=path.replace("\\","/")
    removeEmpty(path)