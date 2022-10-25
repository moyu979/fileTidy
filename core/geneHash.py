from genericpath import isdir
import hashlib
from FileList import *
#用于计算一个文件夹下所有文件的哈希值，返回一个记载所有文件信息的FileList
class GeneHash:
    def __init__(self):
        self.fileList=FileList()
    
    def geneHash(self,file)->FileList:
        af=[]
        if os.path.isdir(file):
            for i in os.listdir(file):
                j=os.path.join(file,i)
                self.geneHash(j)
        else:
            if os.path.getsize(file)>1024**3:
                print("a File more than 1g")
                md5=hashlib.md5()
                with open(file,"rb") as fp:
                    while True:
                        data=fp.read(1024**3)
                        if not data:
                            break
                        md5.update(data)
                fileMd5=md5.hexdigest()
                af.append("hashMd5:\t"+file_md5+"\n")
                af.append("originPath:\t"+file+"\n")
                af.append("end\n")
            else:
                with open(file,"rb") as fp:
                    data=fp.read()
                file_md5=hashlib.md5(data).hexdigest()
                af.append("hashMd5:\t"+file_md5+"\n")
                af.append("originPath:\t"+file+"\n")
                af.append("end\n")
            self.fileList.addAFile(af)
        return self.fileList
    

if __name__ == "__main__":
    print("这个模块不会产生可存储输出，只会将结果输出到控制台，是否继续？")
    yon=input()
    if yon.startswith("y"):
        print("好吧，请输入路径")
        path=input()
        c=GeneHash()
        list=c.geneHash(path)
        list.pOutPut()