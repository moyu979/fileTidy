
import unittest
import os
import remove
import sys
import shutil
sys.path.append("..\\core")
import AFile
import Init
import log
import download
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
        download.afterDownload(dest+"/download")
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
        download.afterDownload(dest+"/download")
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
        download.afterDownload(dest+"/download")
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
        download.afterDownload(dest+"/download")
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
    #删除文件导致的文件丢失没考虑，随做随考虑把        
if __name__ == "__main__":
    unittest.main() 