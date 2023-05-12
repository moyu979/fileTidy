from _FileList import *
from _AZipFile import *
from _Log import *
from _getMoreFile import *
def unzip(fileList:FileList,path,fileStoragePath):

    moreFile=getMoreFile(fileList,fileStoragePath)
    moreFile=GeneHash.run(moreFile)
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
        
        zipFileInList=fileList.findHash(zipFile.hashMd5)
        if not zipFileInList:
            fileList.add(zipFile)
            zipFile.noSourceFile=True
            Log.writeLog("[no Source List]\tfind no source file "+zipFile.hashMd5)
        else:
            if os.path.exists(zipFileInList.nowPath):
                Log.writeLog("[still has file]\t "+zipFile.hashMd5)
            else:
                zipFileInList.removed=True
        
        #处理解压后的文件
        aUnzipFile:AFile
        for aUnzipFile in unzipList:
            unzipFileInList=fileList.findHash(aUnzipFile.hashMd5)
            inMoreFile:AFile=moreFile.findHash(aUnzipFile.hashMd5)
            if unzipFileInList:
                unzipFileInList.removed=False
                unzipFileInList.noSourceFile=False
                unzipFileInList.lossFile=False
                unzipFileInList.unzipFrom.add(zipFileInList.hashMd5)
                
                
                #说明moreFile多了,直接删了就好
                #如果一个文件下载之后没登记，又不幸和解压的某个文件撞了，这个文件有可能被删除
                if inMoreFile:
                    removeFile(inMoreFile)

            else:
                #很正常，解压之后多了
                if inMoreFile:
                    inMoreFile.unzipFrom.add(zipFileInList.hashMd5)
                    fileList.add(inMoreFile)
                #但是如果现在，多的都没找到，问题就大了
                else:
                    Log.writeLog("[unziped File not found]\t"+aUnzipFile.hashMd5+"\t"+aUnzipFile.nowPath)
        
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
        unzip(fileList,path,pathF)

