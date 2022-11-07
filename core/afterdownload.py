from distutils import filelist
import time
from FileList import *
from geneHash import *
import sys

from numpy import may_share_memory
class afterdownload:
    def __init__(self):
        self.filelist=FileList()
        
    def afterDownload(self,path):
        g=GeneHash()
        files=g.geneHash(path)
        self.filelist.importFileList("fileDirs/downloads/new.txt")
        
        sameFile=self.filelist.combine(files.fileList)
        
        time_tuple = time.localtime(time.time())
        
        name="fileDirs/downloads/"
        for i in range(0,6):
            name=name+str(time_tuple[i])
        name=name+".txt"
        
        self.filelist.outPut(name)
        self.filelist.outPut("fileDirs/downloads/new.txt")
        
        
        with open("fileDirs/temp/samefile.txt",'w') as d:
            d.writelines(sameFile)
                  
if __name__ == "__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        print("请输入下载文件存储路径")
        path=input()
        
    aft=afterdownload()
    aft.afterDownload(path)