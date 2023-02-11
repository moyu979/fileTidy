import os
from FileTime import *
def writeLog(string):
    if not os.path.exists("./fileLogs/logs.txt"):
        with open("./fileLogs/logs.txt","w",encoding="utf-8") as s:
            s.write(FileTime()+"\n")
    logfile=open("./fileLogs/logs.txt","a",encoding="utf-8")
    logfile.write(string+"\n")
    logfile.close()
def writeTemp(string,temps="temps.txt"):
    if not os.path.exists("./fileLogs/"+temps):
        with open("./fileLogs/"+temps,"w",encoding="utf-8") as s:
            s.write(FileTime()+"\n")
    logfile=open("./fileLogs/"+temps,"a",encoding="utf-8")
    logfile.write(string+"\n")
    logfile.close()
def writeLogs(string):
    logfile=open("./fileLogs/logs.txt","a",encoding="utf-8")
    for i in string:
        logfile.write(i+"\n")
    logfile.close()
def printAndLog(string):
    print(string)
    writeLog(string)
def printAndLogs(string):
    for i in string:
        print(i)
    writeLogs(string)
if __name__=="__main__":
    while(True):
        i=input("请输入测试字段，以q结束")
        