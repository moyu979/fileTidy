import os
from _fileTime import *
class Log:
    logFile=None
    debugOutput=True
    @classmethod
    def writeLog(cls,string,new_line=True):
        if cls.logFile==None:
            open("./")
        cls.logFile.write(string)
        if new_line:
            cls.logFile.write("\n")
        cls.logFile.flush()
        print(string)

    @classmethod
    def open(cls,path,time=fileTimeSecond().replace(" ","_")):
        log_dir=os.path.join(path,"logs")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        log_path=os.path.join(log_dir,time+"_log.txt")
        if(cls.logFile==None):
            cls.logFile=open(log_path,"w",encoding="utf-8")
        else:
            cls.logFile=open(log_path,"a",encoding="utf-8")
    @classmethod
    def writeLogs(cls,string):
        for i in string:
            cls.writeLog(i)
        cls.logFile.flush()

    @classmethod    
    def closeLog(cls):
        if cls.logFile!=None:
            cls.logFile.flush()
            cls.logFile.close()    
        cls.logFile=None
    @classmethod   
    def debug(cls,string):
        if cls.debugOutput:
            cls.writeLog(string)
            
if __name__=="__main__":
    while(True):
        i=input("请输入测试字段，以q结束")
        Log.writeLog(i)