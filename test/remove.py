import os
def remove(path):
    if os.path.isdir(path):
        list=os.listdir(path)
        for i in list:
            absp=os.path.join(path,i)
            remove(absp)
        os.rmdir(path)
    else:
        os.remove(path)
