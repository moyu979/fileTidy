import sys
class afterdownload:
    def __init__(self,path:str):
        self.path=path
        self.filelist=FileList()
if __name__ == "__main__":
    if len(sys.argv)==1:
        os.path.abspath(".")