import unittest
import os
import sys
import shutil
import time
p=os.path.abspath("core")
sys.path.append(p)
import _AFile
import _AZipFile
import _FileList
import _getMoreFile
import _Hash
import _Log
import compareFile
import fileTime
import init
import RemoveFile
import updateDelete
import updateUnzip
import updateFileList
from remove import *
from compareFile import *
class test(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)

    def tearDown(self) -> None:
        Log.closeLog()
        if os.path.exists("./testFiles"):
            remove("./testFiles") 
        if os.path.exists("./fileLogs"):
            remove("./fileLogs") 
        return super().tearDown()
    
        pass

    def test_updateFileList_download_appendNewFile(self):
        filePath="./test/examples/updateFileList_download_appendNewFile/files"
        destFilePath="./testFiles"
        shutil.copytree(filePath,destFilePath)
        logPath="./test/examples/updateFileList_download_appendNewFile/logs"
        destLogPath="./fileLogs"
        shutil.copytree(logPath,destLogPath)
        updateFileList.update(destFilePath,"download")
        ansPath="./test/examples/updateFileList_download_appendNewFile/ans.txt"
        resPath="./fileLogs/download/new.txt"
        self.assertTrue(compareFile(ansPath,resPath))  

    def test_updateFileList_download_awakeRemoved(self):
        filePath="./test/examples/updateFileList_download_awakeRemoved/files"
        destFilePath="./testFiles"
        shutil.copytree(filePath,destFilePath)

        logPath="./test/examples/updateFileList_download_awakeRemoved/logs"
        destLogPath="./fileLogs"
        shutil.copytree(logPath,destLogPath)

        updateFileList.update(destFilePath,"download")
        ansPath="./test/examples/updateFileList_download_awakeRemoved/ans/download.txt"
        resPath="./fileLogs/download/new.txt"
        self.assertTrue(compareFile(ansPath,resPath))   
        pl="./fileLogs/log"
        pls=os.listdir(pl)
        i:str
        for i in pls:
            if i!="example":
                resPath=os.path.join(pl,i)
        ansPath="./test/examples/updateFileList_download_awakeRemoved/ans/log.txt"
        self.assertTrue(compareFile(ansPath,resPath)) 

    def test_updateFileList_download_moveFiles(self):
        filePath="./test/examples/updateFileList_download_moveFiles/files"
        destFilePath="./testFiles"
        shutil.copytree(filePath,destFilePath)
        logPath="./test/examples/updateFileList_download_moveFiles/logs"
        destLogPath="./fileLogs"
        shutil.copytree(logPath,destLogPath)
        updateFileList.update(destFilePath,"download")
        ansPath="./test/examples/updateFileList_download_moveFiles/ans.txt"
        resPath="./fileLogs/download/new.txt"
        self.assertTrue(compareFile(ansPath,resPath))

    def test_updateFileList_download_newDownloadFile_And_multiRun(self):
        init.init()
        filePath="./test/examples/updateFileList_download_newDownloadFile/files"
        destPath="./testFiles"
        shutil.copytree(filePath,destPath)
        updateFileList.update(destPath,"download")
        updateFileList.update(destPath,"download")
        updateFileList.update(destPath,"download")
        ansPath="./test/examples/updateFileList_download_newDownloadFile/ans.txt"
        resPath="./fileLogs/download/new.txt"
        self.assertTrue(compareFile(ansPath,resPath))

    def test_updateFileList_download_removeSame(self):
        filePath="./test/examples/updateFileList_download_removeSame/files"
        destPath="./testFiles"
        shutil.copytree(filePath,destPath)

        logPath="./test/examples/updateFileList_download_removeSame/logs"
        destLogPath="./fileLogs"
        shutil.copytree(logPath,destLogPath)

        updateFileList.update(destPath,"download")

        ansPath="./test/examples/updateFileList_download_removeSame/ans/download.txt"
        resPath="./fileLogs/download/new.txt"
        self.assertTrue(compareFile(ansPath,resPath))

        pl="./fileLogs/log"
        pls=os.listdir(pl)
        i:str
        for i in pls:
            if i!="example":
                resPath=os.path.join(pl,i)
        ansPath="./test/examples/updateFileList_download_removeSame/ans/log.txt"
        self.assertTrue(compareFile(ansPath,resPath)) 


if __name__=="__main__":
    unittest.main()