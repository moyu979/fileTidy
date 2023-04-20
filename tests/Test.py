import unittest
import os
import sys
import shutil
#sys.path.append("..\\core2")
import _AFile
import init
import _Log
import Download
import Tidy
import _AZipFile
import RemoveFile
import Premove
import aftermove
def remove(path):
    if os.path.isdir(path):
        list=os.listdir(path)
        for i in list:
            absp=os.path.join(path,i)
            remove(absp)
        os.rmdir(path)
    else:
        os.remove(path)
class test(unittest.TestCase):
    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        
    def tearDown(self):
        if os.path.exists("./testFiles"):
            remove("./testFiles") 
        if os.path.exists("./fileLogs"):
            remove("./fileLogs") 
            
    # def test_log_writeLog(self):
    #     os.mkdir("./fileLogs")
    #     log1="aaa"
    #     log2=["bbb","ccc"]
    #     log.writeLog(log1)
    #     log.writeLogs(log2)
    #     log.printAndLog(log1)
    #     log.printAndLogs(log2)
    #     with open("./fileLogs/logs.txt") as result:
    #         res=result.readlines()
    #     with open("testExamples/log_writeLog/logtest.txt") as answer:
    #         ans=answer.readlines()
    #     self.assertEqual(res[1:],ans)
        
    # def test_log_writeTemp(self):
    #     os.mkdir("./fileLogs")
    #     log1="aaa"
    #     log.writeTemp(log1,"n.txt")
    #     with open("./fileLogs/n.txt") as result:
    #         res=result.readlines()
    #     self.assertEqual(res[1],"aaa\n")
        
    def test_download_once(self):
        logSource="testExamples/download_once/fileLogs"
        logDest="./fileLogs"
        fileSource="testExamples/download_once/testFiles"
        fileDest="./testFiles"
        shutil.copytree(logSource,logDest)
        shutil.copytree(fileSource,fileDest)
        Download.download(fileDest)
        Download.download(fileDest)
        with open("./fileLogs/download/new.txt",encoding="utf-8") as res:
            r=res.readlines()
        with open("testExamples/download_once/results/new.txt",encoding="utf-8") as ans:
            a=ans.readlines()   
        self.assertEqual(len(r),len(a),msg="文件长度不相等")
        self.replacePath(r)
        self.assertEqual(r,a)
        
    # def test_download_same(self):
    #     logSource="testExamples/download_same/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/download_same/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     download.download(fileDest)
    #     download.download(fileDest)
    #     with open("./fileLogs/download/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/download_same/results/new.txt",encoding="utf-8") as ans:
    #         a=ans.readlines()   
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)    
        
    # def test_tidy_move(self):
    #     logSource="testExamples/tidy_move/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/tidy_move/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     Tidy.AfterTidy(fileDest)
    #     with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_move/results/tidy.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    
    # def test_tidy_zip(self):
    #     logSource="testExamples/tidy_zip/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/tidy_zip/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     Tidy.AfterTidy(fileDest)
    #     with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_zip/results/tidy.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    #     with open("./fileLogs/download/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_zip/results/download.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    
    # def test_tidy_zip_dual(self):
    #     logSource="testExamples/tidy_zip_dual/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/tidy_zip_dual/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     Tidy.AfterTidy(fileDest)
    #     with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_zip_dual/results/tidy.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    #     with open("./fileLogs/download/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_zip_dual/results/download.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    
    # def test_tidy_zip_nosource(self):
    #     logSource="testExamples/tidy_zip_nosource/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/tidy_zip_nosource/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     Tidy.AfterTidy(fileDest)
    #     with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_zip_nosource/results/tidy.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    #     with open("./fileLogs/download/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_zip_nosource/results/download.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    
    # def test_tidy_zip_lossFile(self):
    #     logSource="testExamples/tidy_zip_lossFile/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/tidy_zip_lossFile/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     Tidy.AfterTidy(fileDest)
    #     with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_zip_lossFile/results/tidy.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
        
    #     with open("./fileLogs/download/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_zip_lossFile/results/download.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    
    # def test_tidy_unzip(self):
    #     logSource="testExamples/tidy_unzip/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/tidy_unzip/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     Tidy.AfterTidy(fileDest)
    #     with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_unzip/results/tidy.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    #     with open("./fileLogs/download/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_unzip/results/download.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    
    # def test_tidy_unzip_lossFile(self):
    #     logSource="testExamples/tidy_unzip_lossFile/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/tidy_unzip_lossFile/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     Tidy.AfterTidy(fileDest)
    #     with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_unzip_lossFile/results/tidy.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    #     with open("./fileLogs/download/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_unzip_lossFile/results/download.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    
    # def test_tidy_unzip_dual(self):
    #     logSource="testExamples/tidy_unzip_dual/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/tidy_unzip_dual/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     Tidy.AfterTidy(fileDest)
    #     with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_unzip_dual/results/tidy.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    #     with open("./fileLogs/download/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_unzip_dual/results/download.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    
    # def test_tidy_unzip_nosource(self):
    #     logSource="testExamples/tidy_unzip_nosource/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/tidy_unzip_nosource/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     Tidy.AfterTidy(fileDest)
    #     with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_unzip_nosource/results/tidy.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    #     with open("./fileLogs/download/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/tidy_unzip_nosource/results/download.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
        
    # def test_premove(self):
    #     logSource="testExamples/premove/fileLogs"
    #     logDest="./fileLogs"
    #     shutil.copytree(logSource,logDest)
    #     path=Premove.premove()
    #     with open("./fileLogs/premove/"+path,encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/premove/fileLogs/premove/new.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    
    # def test_premove_sameHash(self):
    #     logSource="testExamples/premove_sameHash/fileLogs"
    #     logDest="./fileLogs"
    #     shutil.copytree(logSource,logDest)
    #     path=Premove.premove()
    #     with open("./fileLogs/premove/"+path,encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/premove_sameHash/results/premove.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
        
    # def test_aftermove(self):
    #     logSource="testExamples/aftermove/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/aftermove/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     aftermove.aftermove("./testFiles/final")
    #     with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/aftermove/results/tidy.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
        
    #     with open("./fileLogs/final/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/aftermove/results/final.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    # def test_aftermove_moreFile(self):
    #     logSource="testExamples/aftermove_moreFile/fileLogs"
    #     logDest="./fileLogs"
    #     fileSource="testExamples/aftermove_moreFile/testFiles"
    #     fileDest="./testFiles"
    #     shutil.copytree(logSource,logDest)
    #     shutil.copytree(fileSource,fileDest)
    #     aftermove.aftermove("./testFiles/final")
    #     with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/aftermove_moreFile/results/tidy.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
        
    #     with open("./fileLogs/final/new.txt",encoding="utf-8") as res:
    #         r=res.readlines()
    #     with open("testExamples/aftermove_moreFile/results/final.txt",encoding="utf-8") as ans:
    #         a=ans.readlines() 
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     self.replacePath(r)
    #     self.assertEqual(r,a)
    # def replacePath(self,path):
    #     nowPath=os.path.abspath("")
    #     for i in range(0,len(path)):
    #         path[i]=path[i].replace(nowPath+"\\","")
    #         path[i]=path[i].replace(nowPath+"/","")
    #         path[i]=path[i].replace("./","")
    #     pass
    
    
    
if __name__=="__main__":
    unittest.main() 