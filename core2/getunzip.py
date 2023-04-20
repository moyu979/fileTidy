from _FileList import *
from _AZipFile import *
from _Log import *
def getunzip(fileList:FileList,path,writeable=True):
    paths=os.listdir(path)
    unzipList=[]
    for i in paths:
        f=AZipFile(i)
        unzipList.append(f)
    i:AZipFile
    for i in unzipList:

        zfile=fileList.findHash(i.zipFile[0])
        if not zfile:
            zfile=AFile()
            fileList.append(zfile)
            zfile.hashMd5=i.zipFile[0]
            zfile.noSourceFile=True
            _Log.writeLog=("[getUnzip]\t"+i.zipFile[0]+"::"+i.zipFile[0])        

        for j in i.unzipFileList:
            uzFile=fileList.findHash(j[0])
            if not uzFile:
                fileList.append(uzFile)
                uzFile=AFile()
                uzFile.hashMd5=j[0]
            uzFile.unzipFrom.add(i.zipFile)
            uzFile.nowPath=j[1]


