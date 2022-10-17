from FileList import *
from generateHash import *
from RemoveSameHash import *
from CheckMove import *

if __name__ == "__main__":
    #g=GeneHash()
    #g.geneHash("temp/1")
    #g.pOutPut()
    #g.outPut("temp/dest/3.txt")
    
    #r=RemoveSameHash()
    #r.checkHash("temp/dest/3.txt","temp/dest")
    c=CheckMove()
    c.check("temp/dest/before.txt","temp/dest/after.txt","temp/dest/ans.txt")




