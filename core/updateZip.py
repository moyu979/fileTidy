from _FileList import *
from _AZipFile import *
from _Log import *
from _getMoreFile import *
def zip(fileList:FileList,path,fileStoragePath):

    moreFile=getMoreFile(fileList,fileStoragePath)

    paths=os.listdir(path)
    unzipList=[]
    for i in paths:
        f=AZipFile(i)
        unzipList.append(f)
    i:AZipFile

    for i in unzipList:

        zipFile:AFile=i.zipFile
        unzipList:FileList=i.unzipFileList

        #处理压缩文件
        
        inFileList=fileList.findHash(zipFile.hashMd5)
        inMoreFile=moreFile.findHash(zipFile.hashMd5)
        #原来就有，原位修改
        if inFileList:
            #两个都有 多出来了
            if inMoreFile:
                removeFile(inMoreFile)
            for unzipFile in unzipList:
                inFileList.zipFrom.add(unzipFile)
            inFileList.noSourceFile=False
        else:
            if inMoreFile:
                for unzipFile in unzipList:
                    inFileList.zipFrom.add(unzipFile)
                fileList.append(inMoreFile)
        
        #处理解压后的文件
        aUnzipFile:AFile
        for aUnzipFile in unzipList:
            inFileList=fileList.findHash(aUnzipFile.hashMd5)
            if inFileList:
                if os.path.exists(inFileList.nowPath):
                    Log.writeLog("[still has file]\t"+inFileList.hashMd5)
                else:
                    inFileList.removed=True
            else:
                aUnzipFile.removed=True
                aUnzipFile.noSourceFile=True
                fileList.append(aUnzipFile)
        
        fileList.writeBack()


if __name__=="__main__":
    if len(sys.argv)==4:
        path=sys.argv[1]
        pathF=sys.argv[2]
        dataList=sys.argv[3]
    else:
        path=input("请输入存储解压对的文件路径")
        pathF=input("请输入改变的文件的路径")
        dataList=input("解压自哪个文件夹")
    Log.writeLog("unzip "+path+" from "+dataList)
    path=os.path.abspath(path)
    fileList=None
    if dataList=="download":
        fileList=FileList("fileLogs/download/new.txt")
    elif dataList=="tidy":
        fileList=FileList("fileLogs/tidy/new.txt")
    elif dataList=="final":
        fileList=FileList("fileLogs/final/new.txt")   
    else:
        Log.writeLog("[para error]\tnot found fileList named "+path)
    if fileList!=None:
        zip(fileList,path,pathF)

