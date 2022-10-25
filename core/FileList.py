from AFile import *

def return_now_path(elem:AFile):
    return elem.nowPath
def return_hash(elem:AFile):
    return elem.hashMd5

class FileList:
    def __init__(self,path=None) -> None:
        self.fileList:AFile=[]
        if not path==None:
            self.importFileList(path)
    
    def importFileList(self,path):
        inFile=open(path,encoding="utf-8")
        af=[]
        aline:str=inFile.readline()
        while aline:
            if aline.startswith("end\n") or aline == "\n":
                if not af==[]:
                    self.fileList.append(AFile(af))
                af=[]
            else:
                af.append(aline)
            aline=inFile.readline()
            
    
    
    def sortBypath(self):
        self.fileList.sort(key=return_now_path)
        
    def sortByHash(self):
        self.fileList.sort(key=return_hash)
    #增
    def combine(self,files):
        for i in files:
            self.addAFile(i)
            
    def addAFile(self,paras):
        if not type(paras).__name__=="AFile":
            a=AFile(paras)
        else:
            a=paras
            
        file=self.findHash(a.hashMd5)
        
        if not file==None:
            file.insertOriginPath(a.originPath)
            file.insertunzip(a.unzip)
            file.insertzip(a.zip)
            file.insertremoved(a.removed)
        else:
            self.fileList.append(a)
        
    #删
    def deleteByHash(self,Hash):
        i:AFile
        for i in self.fileList:
            if i.hashMd5==Hash:
                self.fileList.remove(i)
                
    #查
    def findHash(self,hash)->AFile:
        for i in self.fileList:
            if i.hashMd5==hash:
                return i
        return None
    
    def outPut(self,path):
        outFile=open(path,'w',encoding="utf-8")
        for i in self.fileList:
            outFile.write(str(i))
        outFile.flush()
        outFile.close()
        
    def pOutPut(self):
        for i in self.fileList:
            print(i)

if __name__ =="__main__":
    print("this is a file list so dont use it")