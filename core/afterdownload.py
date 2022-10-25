from distutils import filelist
import time
from FileList import *
from geneHash import *
import sys
class afterdownload:
    def __init__(self,path:str):
        self.path=path
        self.filelist=FileList()
        
    def afterDownload(self,path):
        g=GeneHash()
        files=g.geneHash(path)
        self.filelist.importFileList("../fileDirs/downloads")
        self.filelist.combine(files)
        time_tuple = time.localtime(time.time())
        name="../fileDirs/downloads/"
        for i in range(0,6):
            name=name+str(time_tuple[i])
        name=name+".txt"
        self.filelist.outPut(name)
        self.filelist.outPut("../fileDirs/downloads/new.txt")
         
        
        
    
    
if __name__ == "__main__":
    if len(sys.argv)==1:
        os.path.abspath(".")