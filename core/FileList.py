

from AFile import *

def return_now_path(elem:AFile):
    return elem.nowPath
def return_hash(elem:AFile):
    return elem.hashMd5
class FileList:
    def __init__(self) -> None:
        self.fileList=[]
    
    def importFileList(self,path):
        inFile=open(path,encoding="utf-8")
        af=[]
        aline:str=inFile.readline()
        while aline:
            if aline.startswith("end\n") or aline == "\n":
                self.fileList.append(AFile(af))
                af=[]
            else:
                af.append(aline)
            aline=inFile.readline()

    def sort(self):
        self.fileList.sort(key=return_now_path)
    def sortInHash(self):
        self.fileList.sort(key=return_hash)
    def addAFile(self,paras):
        a=AFile(paras)
        self.fileList.append(a)

    def outPut(self,path):
        outFile=open(path,'w',encoding="utf-8")
        for i in self.fileList:
            outFile.write(str(i))
        outFile.flush()
        outFile.close()

    def pOutPut(self):
        for i in self.fileList:
            print(i)

    def existHash(self,hash):
        for i in self.fileList:
            if i.hashMd5==hash:
                return True
        return False



if __name__ =="__main__":
    print("this is a file list so dont use it")