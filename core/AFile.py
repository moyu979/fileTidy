

import os.path
class AFile:
    def __init__(self,paras:str) -> None:
        self.hashMd5=None
        self.nowName=None
        self.nowPath=None
        self.originPath=[]
        self.changePath=[]
        self.sameAs=[]
        self.unzip=[]
        self.zip=[]

        for para in paras:
            plist=para.split(":\t")
            #md5��¼��(Ψһ)
            if plist[0] == 'hashMd5':
                self.hashMd5=plist[1]
            #ԭʼĿ¼��
            if plist[0] == 'originPath':
                self.originPath.append(plist[1])
            #��ͬ��(��ʷ����)
            if plist[0] == 'sameAs':
                self.originPath.append(plist[1])
            #·����Ǩ
            if plist[0] == 'changePath':
                self.changePath.append(plist[1])
            #��ѹ��
            if plist[0] == 'unzipFrom':
                self.unzip.append(plist[1])
            #ѹ����
            if plist[0] == 'zipTo':
                self.zip.append(plist[1])

        if len(self.changePath)==0:
            self.nowPath = self.originPath[0]
        else:
            self.nowPath=self.changePath[-1]

        self.nowName=os.path.basename(self.nowPath)

    def __str__(self) -> str:
        string="hashMd5:\t"+self.hashMd5
        string=string+"nowName:\t"+self.nowName
        string=string+"nowPath:\t"+self.nowPath

        for i in self.originPath:
            string=string+"originPath:\t"+i

        for i in self.changePath:
            string=string+"changePath:\t"+i

        for i in self.unzip:
            string=string+"unzip:\t"+i

        for i in self.zip:
            string=string+"zip:\t"+i

        string=string+"end\n"
        return string


if __name__ == "__main__":
    print("testing")
    string=["hashMd5:\ttest",
            "originPath:\t/mnt/test/test.txt",
            "changePath:\tdddd/dddd/dddd/dd.txt",
            "changePath:\teeee/eeee/eeee/ded.txt"]
    a=AFile(string)
    print (a)



        





