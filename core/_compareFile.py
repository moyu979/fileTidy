import sys
import os

def compare(path1,path2):
    path1=os.path.abspath(path1)
    path2=os.path.abspath(path2)
    if os.path.isdir(path1) and os.path.isdir(path2):    
        f1=os.listdir(path1)
        f2=os.listdir(path2)
        for i in f1:
            if not i in f2:
                return False
            else:
                absSubPath1=os.path.join(path1,i)
                absSubPath2=os.path.join(path2,i)
                if not compare(absSubPath1,absSubPath2):
                    return False
        return True
    elif os.path.isdir(path1) ^ os.path.isdir(path2):
        return False
    else:
        return compareFile(path1,path2)
#当且仅当两个文件不是同一个但内容相同时返回True    
def compareFile(path1,path2)->bool:
    ret=False
    #进入比较流程
    f1=open(path1,"rb")
    f2=open(path2,"rb")
    while True:
        #以512M为单位比较
        data1=f1.read(1024**2*512)
        data2=f2.read(1024**2*512)
        
        #如果到尽头都相同，视作文件相同
        if not data1 and not data2:
            ret=True
            break
        #如果出现不同，视作文件不同
        if not data1==data2:
            ret=False
            break        
    f1.close()
    f2.close()
    return ret
        
if __name__=="__main__":
    if len(sys.argv)!=3:
        print("请输入第一个文件的位置")
        path1=input()
        print("请输入第二个文件的位置")
        path2=input()
    else:
        path1=sys.argv[1]
        path2=sys.argv[2]
    path1=os.path.abspath(path1)
    path2=os.path.abspath(path2)
    path1=path1.replace("\\","/")
    path2=path2.replace("\\","/")    
    if compare(path1,path2):
        print("相同")
    else:
        print("不同")
        