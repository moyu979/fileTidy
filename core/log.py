def write(paras):
    myfile=open("../fileDirs/log.txt","a",encoding="utf-8")
    if type(paras).__name__=="list":
        for i in paras:
            myfile.write(i)
    else:
        myfile.write(paras)
                
if __name__=="__main__":
    write(["测试写1\n","测试写2\n"])
    print("测试完成")