from AFile import *
import os
import log
import sys
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
    log.writeLog("[remove file]remove "+filePath+"with hash "+file.hashMd5)
    os.remove(filePath)
        
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
        log.writeLog("[remove file]remove "+path)
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
            log.writeTemp("[remove empty]remove "+path,"removeEmpty.txt")
            return
        
if __name__ == "__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入要检查的文件或文件夹")
    path=os.path.abspath(path)
    removeEmpty(path)