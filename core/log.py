class Log:
    def __init__(self) -> None:
        self.logfile=open("./fileDirs/logs.txt","a",encoding="utf-8")
        self.logbuff=[]
        
    def writeLog(self,string):
        self.logbuff.append(string+"\n")
        
    def __del__(self):
        self.logfile.writelines(self.logbuff)
        self.logfile.flush()
        self.logfile.close()
        
if __name__=="__main__":
    log=Log()
    while(True):
        i=input("请输入测试字段，以q结束")
        if i=="q":
            break
        else:
            log.writeLog(i)
        