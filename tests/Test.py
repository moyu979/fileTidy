
import unittest
import os
import remove
import sys
import shutil
sys.path.append("..\\core")
import AFile
import Init
import Log
import Download
import Tidy
import AZipFile
def AFileSame(a:AFile,b:AFile):
    if a.hashMd5 != b.hashMd5:
        return False
    if a.sameHashCount!=b.sameHashCount:
        return False
    if a.removed != b.removed:
        return False
    if a.originPath.len()!=b.originPath.len():
        return False
class test(unittest.TestCase):
    def setUp(self):
        Init.init()
    def tearDown(self):
        remove.remove("./fileLogs")
        if os.path.exists("./testFiles"):
            remove.remove("./testFiles") 
    #测试初始化是否成功
    def test_init(self):
        files=["download","final","tidy"]
        ans=open("testExamples/init/new.txt")
        a=ans.read()
        for i in files:
            real=os.path.join("./fileLogs",i)
            self.assertTrue(os.path.exists(real),msg=i+" not exist")
            new=os.path.join(real,"new.txt")
            self.assertTrue(os.path.exists(new),msg=i+"/new.txt"+" not exist")
            with open(new) as ne:
                n=ne.read()
            self.assertTrue(n==a,msg=new+"not same")
        ans.close()
        
    def test_log(self):
        log1="aaa"
        log2=["bbb","ccc"]
        Log.writeLog(log1)
        Log.writeLogs(log2)
        Log.printAndLog(log1)
        Log.printAndLogs(log2)
        
        with open("./fileLogs/logs.txt") as result:
            res=result.readlines()
        with open("testExamples/log/logtest.txt") as answer:
            ans=answer.readlines()
        
        self.assertEqual(res[1:],ans)
        
    def test_download(self):
        source="testExamples/download/files"
        dest="./testFiles"
        shutil.copytree(source,dest)
        #重复两遍看效果
        Download.afterDownload(dest)
        Download.afterDownload(dest)
        with open("./fileLogs/download/new.txt",encoding="utf-8") as res:
            r=res.readlines()
        with open("testExamples/download/new.txt",encoding="utf-8") as ans:
            a=ans.readlines()   
        self.assertEqual(len(r),len(a),msg="文件长度不相等")
        for i in range(0,len(a)):
            rl=r[i].split(":\t")
            al=a[i].split(":\t")
            if rl[0].endswith("Path"):
                self.assertTrue(rl[1].endswith(al[1]),msg="line "+str(i+1)+" not same")
            else:
                self.assertEqual(rl[-1],al[-1],msg="line "+str(i+1)+" not same")
    # #两次接续增加
    # # def test_download_doubleadd(self):
    # #     pass
    
    def test_AZipFileError(self):
        source="testExamples/azipfile_errorzip/files"
        dest="./testFiles"
        shutil.copytree(source,dest)
        dest=os.path.abspath(dest)
        a=AZipFile.AZipFile(dest)
        with open("./testExamples/azipfile_errorzip/new.txt",encoding="utf-8") as ans:
            a=ans.readlines()[0]
        with open("./fileLogs/logs.txt",encoding="utf-8") as res:
            r=res.readlines()[1]
        print(r)
        abspath=os.path.abspath(dest)
        r2=r.replace(abspath,"")+"\n"
        a=a.replace("\n","")
        r2=r2.replace("\n","")
        self.assertEqual(r2,a)
        
    #解压文件的test
    def test_tidyzip(self):   
        source="testExamples/tidy_zip/files"
        dest="./testFiles"
        shutil.copytree(source,dest)
        Download.afterDownload(dest+"/download")
        Tidy.AfterTidy(dest+"/tidy")
        with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
            r=res.readlines()
        with open("./testExamples/tidy_zip/new.txt",encoding="utf-8") as ans:
            a=ans.readlines()
        abspath=os.path.abspath(dest)
        k=[]
        for i in r:
            l=i.replace(abspath,"")
            k.append(l)
        self.assertEquals(k,a)
    # #压缩文件的test
    def test_tidyunzip(self):
        source="testExamples/tidy_unzip/files"
        dest="./testFiles"
        shutil.copytree(source,dest)
        Download.afterDownload(dest+"/download")
        Tidy.AfterTidy(dest+"/tidy")
        with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
            r=res.readlines()
        with open("./testExamples/tidy_unzip/new.txt",encoding="utf-8") as ans:
            a=ans.readlines()
        abspath=os.path.abspath(dest)
        k=[]
        for i in r:
            l=i.replace(abspath,"")
            k.append(l)
        self.assertEquals(k,a)
    #一个文件来自两个压缩包的test
    def test_multiunzip(self):
        source="testExamples/tidy_mutilunzip/files"
        dest="./testFiles"
        shutil.copytree(source,dest)
        Download.afterDownload(dest+"/download")
        Tidy.AfterTidy(dest+"/tidy")
        with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
            r=res.readlines()
        with open("./testExamples/tidy_mutilunzip/new.txt",encoding="utf-8") as ans:
            a=ans.readlines()
        abspath=os.path.abspath(dest)
        k=[]
        for i in r:
            l=i.replace(abspath,"")
            k.append(l)
        self.assertEquals(k,a)
    #删除文件测试
    def test_tidy_remove(self):   
        source="testExamples/tidy_delete/files"
        dest="./testFiles"
        shutil.copytree(source,dest)
        Download.afterDownload(dest+"/download")
        Tidy.AfterTidy(dest+"/tidy")
        with open("./fileLogs/tidy/new.txt",encoding="utf-8") as res:
            r=res.readlines()
        with open("./testExamples/tidy_delete/new.txt",encoding="utf-8") as ans:
            a=ans.readlines()
        abspath=os.path.abspath(dest)
        k=[]
        for i in r:
            l=i.replace(abspath,"")
            k.append(l)
        self.assertAlmostEquals(k,a)
    
    
        
                
            
if __name__ == "__main__":
    unittest.main() 