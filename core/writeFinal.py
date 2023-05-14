from _FileList import *
from _AZipFile import *
from _Log import *
from _getMoreFile import *

def final(path):
    finalFileList=FileList("./fileLogs/final/new.txt")
    downloadFileList=FileList("./fileLogs/download/new.txt")

    notExist=getMoreFile(finalFileList,path)

    notExistHash=GeneHash().run(notExist)

    i:AFile
    for i in notExistHash:
        finalFile=finalFileList.findHash(i.hashMd5)
        downloadFile=downloadFileList.findHash(i.hashMd5)

        if not finalFile and not downloadFile:
            i.noSourceFile=True
            finalFileList.append(i)
        elif not finalFile and downloadFile:
            downloadFile.changePath.append(i.nowPath)
            downloadFile.removed=False
            finalFileList.append(downloadFile)
        elif finalFile and not downloadFile:
            if os.path.exists(finalFile.nowPath):
                i.originPath=None
                finalFileList.appendNoSame(i)
            else:
                finalFile.changePath.append(i.nowPath)
        else:
            finalFile.originPath.add(downloadFile.originPath)
            finalFile.zipFrom.add(downloadFile.zipFrom)
            finalFile.unzipFrom.add(downloadFile.unzipFrom)
            if os.path.exists(finalFile.nowPath):
                if finalFile.noSourceFile:
                    finalFile.noSourceFile=downloadFile.noSourceFile
                    i.originPath=None
                    finalFileList.appendNoSame(i)
            else:
                finalFile.changePath.append(i.nowPath)

        if downloadFile:
            downloadFileList.deleteByHash(downloadFile.hashMd5)

    downloadFileList.writeBack()
    finalFileList.writeBack()

if __name__=="__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入最终文件存储路径")
    Log.writeLog("update final with "+path)
    path=os.path.abspath(path)
    final(path)
