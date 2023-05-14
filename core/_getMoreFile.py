from _FileList import *
from _AZipFile import *
from _Hash import *
from _Log import *

#返回多出来的文件列表和哈希值
def getMoreFile(fileList:FileList,path):
    nowInFile=[]
    notInFileList=[]
    #收集目录下所有文件路径
    for curDir, dirs, files in os.walk(path):
        for file in files:
            if file!="redirect.txt":
                p=os.path.join(curDir, file)
                nowInFile.append(os.path.abspath(p))

    #找到不存在的文件
    for f in nowInFile:
        if fileList.findPath(f):
            pass
        else:
            notInFileList.append(f)

    #FileNotInList:FileList=GeneHash().run(notInFileList)
    
    return notInFileList





    
