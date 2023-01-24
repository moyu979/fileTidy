def makeText(path=""):
    for i in range(0,3):
        dir=path+"/"+str(i)+".txt"
        with open(dir,"w") as f:
            f.writelines(str(i))

if __name__=="__main__":
    p=input("请输入存储文件")
    makeText(p)