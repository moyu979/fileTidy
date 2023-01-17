from AFile import *
import os
import Log

#将f2的文件删除，在原地的“redirect.txt”文件中记录
def removeFile(file:AFile):
    filePath=file.nowPath
    fileDir=file.nowPath.replace(file.nowName,"")
    redirPath=fileDir+"redirect.txt"
    #存在则打开，不存在则新建
    if os.path.exists(redirPath):
        fp=open(redirPath,"a",encoding="utf-8")
    else:
        fp=open(redirPath,"w",encoding="utf-8")
        fp.write(fileDir)
        fp.write("\n")
        fp.write("\n")
        
    fp.write("hash:\t"+file.hashMd5+"\n")
    fp.write("name:\t"+file.nowName+"\n")
    fp.close()
    os.remove(filePath)
    Log.writeLog("remove "+filePath+"with hash "+file.hashMd5)
    
def removeFiles(file2):
    for i in file2:
        removeFile(i)
        
def remove(path):
    if os.path.isdir(path):
        list=os.listdir(path)
        for i in list:
            absp=os.path.join(path,i)
            remove(absp)
        os.rmdir(path)
    else:
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
            with open ("./removeempty/new.txt","a") as f:
                Log.writeLog("remove "+path)
            return
        
if __name__ == "__main__":
    p=input("请输入路径")
    removeEmpty(p)