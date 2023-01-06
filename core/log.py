logfile=open("./fileLogs/logs.txt","a",encoding="utf-8")
def writeLog(string):
    logfile.write(string+"\n")
def writeLogs(string):
    for i in string:
        writeLog(i)
def printAndLog(string):
    print(string)
    writeLog(string)
def printAndLogs(string):
    for i in string:
        print(i)
        writeLog(i)

def resetLogFile(path):
    logfile.flush()
    logfile.close()
    logfile=open(path,"a",encoding="utf-8")       
if __name__=="__main__":
    while(True):
        i=input("请输入测试字段，以q结束")
        