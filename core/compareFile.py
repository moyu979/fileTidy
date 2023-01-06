import sys
#当且仅当两个文件不是同一个但内容相同时返回True

def compareFile(path1,path2)->bool:
    if(type(path1).__name__=="AFile"):
        path1=path1.nowPath
    if(type(path2).__name__=="AFile"):
        path2=path2.nowPath    
        
    ret=False
    #如果某个文件不存在，直接否
    if path1==None or path2==None:
        return False
    #如果路径相同，说明文件重复，不视作相同文件
    if path1==path2:
        return False
    #进入比较流程
    f1=open(path1,"rb")
    f2=open(path2,"rb")
    while True:
        #以512M为单位比较
        data1=f1.read(1024**2*512)
        data2=f2.read(1024**2*512)
        
        #如果到尽头都相同，视作文件相同
        if not data1:
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
        