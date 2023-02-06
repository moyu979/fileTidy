import os
import re
import log
def innums(path:str,suppath:str):
    if not os.path.isdir(path):
        a=re.match("[1-9]*",suppath)
        b=re.match("cd",path)
        c=re.match("scan",path)
        print(a)
        print(b)
        print(c)
        if a.group()=='' and b==None and c==None:
            return False
        return True
    else:
        ls=os.listdir(path)
        for i in ls:
            pa=os.path.join(path,i)
            if not innums(pa,i):
                log.writeLog("[no number]"+path)
        return True

p=input("请输入文件")
innums(p,"")