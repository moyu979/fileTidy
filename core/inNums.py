import os
import re
import log
import sys
#查看每个文件是否都在以编号为名的目录下
def innums(path:str,suppath:str):
    if not os.path.isdir(path):
        a=re.match("[1-9]*",suppath)
        b=re.match("cd",path)
        c=re.match("scan",path)
        if a.group()=='' and b==None and c==None:
            return False
        return True
    else:
        ls=os.listdir(path)
        for i in ls:
            pa=os.path.join(path,i)
            if not innums(pa,i):
                log.writeTemp("[no number]"+path)
        return True

if __name__ == "__main__":
    if len(sys.argv)==2:
        path=sys.argv[1]
    else:
        path=input("请输入要检查的文件或文件夹")
    path=os.path.abspath(path)
    innums(path)