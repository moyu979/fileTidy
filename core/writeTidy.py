from _FileList import *
from _AFile import *
from _AZipFile import *
from _Hash import *
from _Log import *

def tidy(path):
    inDownLoadList=FileList("./fileLogs/download/new.txt")
    inTidyList=FileList("./fileLogs/tidy/new.txt")
    inFinalList=FileList("./fileLogs/final/new.txt")

    