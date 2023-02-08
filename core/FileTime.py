import time

def FileTime():
    time_tuple = time.localtime(time.time())
    name=""
    for i in range(0,6):
        name=name+str(time_tuple[i])+"_"
    name=name[:-1]
    return name
        