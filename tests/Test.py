
import unittest
import os
import remove
import sys
import shutil
sys.path.append("..\\core")
import Init
import Log
import Download
class test(unittest.TestCase):
    def setUp(self):
        Init.init()
    def tearDown(self):
        remove.remove("./fileLogs")
        if os.path.exists("./testFiles"):
            remove.remove("./testFiles") 
    #测试初始化是否成功
    # def test_init(self):
    #     files=["download","final","tidy"]
    #     ans=open("testExamples/init/new.txt")
    #     a=ans.read()
    #     for i in files:
    #         real=os.path.join("./fileLogs",i)
    #         self.assertTrue(os.path.exists(real),msg=i+" not exist")
    #         new=os.path.join(real,"new.txt")
    #         self.assertTrue(os.path.exists(new),msg=i+"/new.txt"+" not exist")
    #         ne=open(new)
    #         n=ne.read()
    #         self.assertTrue(n==a,msg=new+"not same")
    #         ne.close()
    #     ans.close()
        
    # def test_log(self):
    #     log1="aaa"
    #     log2=["bbb","ccc"]
    #     Log.writeLog(log1)
    #     Log.writeLogs(log2)
    #     Log.printAndLog(log1)
    #     Log.printAndLogs(log2)
        
    #     result=open("./fileLogs/logs.txt")
    #     answer=open("testExamples/log/logtest.txt")
        
    #     res=result.readlines()
    #     ans=answer.readlines()
        
    #     self.assertEqual(res[1:],ans)

    #     result.close()
    #     answer.close()
        
    # def test_download(self):
    #     source="testExamples/download/files"
    #     dest="./testFiles"
    #     shutil.copytree(source,dest)
    #     #重复两遍看效果
    #     Download.afterDownload(dest)
    #     Download.afterDownload(dest)
    #     res=open("./fileLogs/download/new.txt",encoding="utf-8")
    #     ans=open("testExamples/download/new.txt",encoding="utf-8") 
    #     r=res.readlines()
    #     a=ans.readlines()   
    #     res.close()
    #     ans.close()
    #     self.assertEqual(len(r),len(a),msg="文件长度不相等")
    #     for i in range(0,len(a)):
    #         rl=r[i].split(":\t")
    #         al=a[i].split(":\t")
    #         if rl[0].endswith("Path"):
    #             self.assertTrue(rl[1].endswith(al[1]),msg="line "+str(i+1)+" not same")
    #         else:
    #             self.assertEqual(rl[-1],al[-1],msg="line "+str(i+1)+" not same")
    #单纯移动的test
    def test_tidymove(self):
        downloadSource="testExamples/download/files"
        downloadDest="./testFiles"
        Download.afterDownload(dest)
        
        pass
    #解压文件的test
    def test_tidyunzip(self):   
        pass
    #压缩文件的test
    def test_tidyzip(self):
        pass
    #一个文件来自两个压缩包的test
    def test_multiunzip(self):
        pass
    #一个文件向两个压缩包压缩的test
    def test_multizip(self):
        pass
    
    
        
                
            
if __name__ == "__main__":
    unittest.main() 