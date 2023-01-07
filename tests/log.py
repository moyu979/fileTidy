import os
import sys
sys.path.append("..\\core")
import Log

def testLog():
    #写入
    log1="aaa"
    log2=["bbb","ccc"]
    Log.writeLog(log1)
    Log.writeLogs(log2)
    Log.printAndLog(log1)
    Log.printAndLogs(log2)
    Log.logClose()
    result=open("./fileLogs/logs.txt")
    answer=open("./answer/Log/logtest.txt")
    print("---------")
    #跳过日期行
    result.readline()
    r=result.readline()
    a=answer.readline()
    while(a):
        if a==r:
            pass
            r=result.readline()
            a=answer.readline()
        else:
            return False
    if r:
        return False
    else:
        return True

if __name__=="__main__":
    if testLog():
        print("LogTest pass")
    else:
        print("LogTest error")        