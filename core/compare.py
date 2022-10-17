from FileList import *
from AFile import *
f=FileList()
g=FileList()
f.importFileList("./work3/bluelogn.txt")
g.importFileList("./work3/bluen.txt")
h:AFile=g.fileList
for i in h:
    if f.existHash(i.hashMd5):
        pass
    else:
        print("1")

#des=open("./work3/bluen.txt","r",encoding="utf-8")
#sor=open("./work3/bluelogn.txt","r",encoding="utf-8")

#desl=des.readline()
#sorl=sor.readline()

#while desl:
#    #if desl.startswith("hash"):
#    if desl!=sorl:
#        print(desl)
#        print(sorl)
#        input()
#    desl=des.readline()
#    sorl=sor.readline()

