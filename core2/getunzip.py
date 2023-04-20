from FileList import *
from AZipFile import *
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
        
        zfile.removed=True

        for j in i.fileList:
            uzFile=fileList.findHash(j[0])
            if not uzFile:
                uzFile=AFile()
                uzFile.hashMd5=j[0]
            uzFile.unzipFrom.add(i.zipFile)
            uzFile.nowPath=j[1]


