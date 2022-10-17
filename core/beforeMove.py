from posixpath import join
import os
import sys
import hashlib

destList=open("./workPath/destList/dest.txt",'w')

class beforeMove:

def run(nowPath,):
    lists=[]
    
def beforeMove(nowPath,movePath):
    if os.path.isdir(file):
        for i in os.listdir(file):
            j=os.path.join(file,i)
            geneHash(j)
    else:
        if os.path.getsize(file)>1024**3:
            print("more than 1G")
            md5=hashlib.md5()
            with open(file,'rb') as fp:
                while True:
                    data=fp.read(1024**3)
                    if not data:
                        break
                    md5.update(data)
            file_md5=md5.hexdigest()
            goodlog.write("hashMd5:\t"+file_md5+"\n")
            goodlog.write("originPath:\t"+file+"\n\n")
        else:
            with open(file,'rb') as fp:
                data=fp.read()
            file_md5=hashlib.md5(data).hexdigest()
            goodlog.write("hashMd5:\t"+file_md5+"\n")
            goodlog.write("originPath:\t"+file+"\n\n")