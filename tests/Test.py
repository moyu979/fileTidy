import queue
import unittest
import os
import remove
import sys
sys.path.append("..\\core")
import Init
import Log

class test(unittest.TestCase):
    def setUp(self):
        Init.init()
        
    def tearDown(self):
        remove.remove("./fileLogs")
    
    def test_null(self):
        self.assertTrue(True)
    @unittest.skip("passed")    
    def test_init(self):
        files=["download","final","tidy"]
        ans=open("./answer/Init/new.txt")
        a=ans.read()
        for i in files:
            real=os.path.join("./fileLogs",i)
            self.assertTrue(os.path.exists(real),msg=i+" not exist")
            new=os.path.join(real,"new.txt")
            self.assertTrue(os.path.exists(new),msg=i+"/new.txt"+" not exist")
            ne=open(new)
            n=ne.read()
            self.assertTrue(n==a,msg=new+"not same")
    @unittest.skip("passed") 
    def test_log(self):
        log1="aaa"
        log2=["bbb","ccc"]
        Log.writeLog(log1)
        Log.writeLogs(log2)
        Log.printAndLog(log1)
        Log.printAndLogs(log2)
        
        result=open("./fileLogs/logs.txt")
        answer=open("./answer/Log/logtest.txt")
        
        res=result.readlines()
        ans=answer.readlines()
        
        self.assertEqual(res[1:],ans)
        
if __name__ == "__main__":
    unittest.main()