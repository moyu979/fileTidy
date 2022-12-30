import sys
#当且仅当两个文件不是同一个但内容相同时返回True
def compareFile(path1,path2)->bool:
    if path1==path2:
        return False
    
    f1=open(path1,"rb")
    f2=open(path2,"rb")
    
    while True:
        data1=f1.read(1024**2*512)
        data2=f2.read(1024**2*512)
        if not data1:
            return True
        
        if not data1==data2:
            return False
        
if __name__=="__main__":
    print(len(sys.argv))
    if len(sys.argv)!=3:
        print("请输入第一个文件的位置")
        path1=input()
        print("请输入第二个文件的位置")
        path2=input()
    else:
        path1=sys.argv[1]
        path2=sys.argv[2]
    if compareFile(path1,path2):
        print("相同")