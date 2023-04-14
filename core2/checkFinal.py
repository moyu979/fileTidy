from FileList import *
from AFile import *
def checkFinal(finalPath):
    finalRecord=FileList("./fileLog/final/new.txt")
    wrongRemove=[]
    nowFinalPath=[] 
    notFoundFile=[]
    notFoundRecord=[]
    #收集目录下所有文件路径
    for curDir, dirs, files in os.walk(finalPath):
        for file in files:
            if file!="redirect.txt":
                p=os.path.join(curDir, file)
                nowFinalPath.append(os.path.abspath(p))

    for i in nowFinalPath:
        file=finalRecord.findPath(i)
        if file:
            if file.removed:
                wrongRemove.append(file)
            else:
                pass
        else:
            notFoundRecord.append(i)

    for i in finalRecord:
        if os.path.exists(i.nowPath):
            pass
        else:
            notFoundFile.append(i)


    with open("./notRecord.txt","w") as f:
        for i in notFoundRecord:
            f.write(i)
            f.write("\n")

    fi=FileList()
    for i in wrongRemove:
        fi.append(i)
    fi.outPut("./wrongRemove")

    f2=FileList()
    for i in notFoundFile:
        f2.append(i)
    f2.outPut("./notFile")
