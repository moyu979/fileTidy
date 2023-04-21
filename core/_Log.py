import os
from fileTime import *
class Log:
    logFile=None
    @classmethod
    def writeLog(cls,string):
        cls.check()
        cls.logFile.write(string)
        cls.logFile.flush()
    @classmethod
    def check(cls):
        if(cls.logFile==None):
            time=fileTime()
            name="./fileLogs/log/"+time+".txt"
            cls.logFile=open(name,"w",encoding="utf-8")
    @classmethod
    def writeLogs(cls,string):
        for i in string:
            cls.logfile.write(i+"\n")
        cls.logFile.flush()
        
if __name__=="__main__":
    while(True):
        i=input("请输入测试字段，以q结束")
        Log.writeLog(i)